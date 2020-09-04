#!/usr/bin/env python3

###############################################################################
## Dactyl Style Police                                                       ##
## Author: Rome Reginelli                                                    ##
## Copyright: Ripple Labs, Inc. 2016                                         ##
##                                                                           ##
## Reads the markdown files to try and enforce elements of good style.       ##
###############################################################################

from dactyl.common import *

import collections

from bs4 import BeautifulSoup
from bs4 import Comment
from bs4 import NavigableString
import spellchecker

from dactyl.dactyl_build import DactylBuilder
from dactyl.config import DactylConfig
from dactyl.cli import DactylCLIParser
from dactyl.target import DactylTarget
import dactyl.style_report as style_report

OVERRIDE_COMMENT_REGEX = r" *STYLE_OVERRIDE: *([\w, -]+) "
SPELLING_OVERRIDE_REGEX = r" *SPELLING_IGNORE: *([\w, -]+) "

EXTENDED_DICTIONARY = "words.txt"


class DactylStyleChecker:
    def __init__(self, target, config):
        """
        A checker to build a target "virtually" and check its text for specific
        style rules, including discouraged words and phrases, reading scores,
        etc.

        Does not check text in code samples.
        """
        self.target = target
        self.config = config
        self.load_style_rules()
        self.issues = None
        self.load_spellchecker()


    @staticmethod
    def tokenize(passage):
        passage = passage.replace("’", "'") # normalize smart quotes to plain quotes
        passage = re.sub(r"[¹²³½]","",passage)
        words = re.split(r"[^\w']+", passage)
        words = [re.sub("'s?$","",w) for w in words] # strip trailing 's or '
        words = [re.sub("^'","",w) for w in words] # strip leaing '
        return [w for w in words if w]

    @staticmethod
    def depunctuate(passage):
        punctuation = re.compile(r"[,.;()!'\"]")
        return re.sub(punctuation, "", passage)

    def load_style_rules(self):
        """Reads word and phrase substitution files into the config"""
        if "word_substitutions_file" in self.config:
            with open(self.config["word_substitutions_file"], "r", encoding="utf-8") as f:
                self.disallowed_words = yaml.load(f)
        else:
            logger.warning("No 'word_substitutions_file' found in config.")
            self.disallowed_words = {}

        if "phrase_substitutions_file" in self.config:
            with open(self.config["phrase_substitutions_file"], "r", encoding="utf-8") as f:
                self.disallowed_phrases = yaml.load(f)
        else:
            logger.warning("No 'phrase_substitutions_file' found in config.")
            self.disallowed_phrases = {}

    def load_spellchecker(self):
        """
        Load the spelling checker, including a built-in extended dictionary and
        optional project-level configurable word dictionary with words not to
        flag as misspelled.
        """
        self.spell = spellchecker.SpellChecker(distance = 1)

        try:
            with resource_stream(__name__, EXTENDED_DICTIONARY) as f:
                self.load_words_from_file(f)
        except FileNotFoundError as e:
            recoverable_error("Couldn't load Dactyl built-in spelling file. " +
                              "Using the default dictionary only.",
                              self.config.bypass_errors, error=e)

        spelling_file = self.config.get("spelling_file", None)
        if not spelling_file:
            logger.debug("No spelling_file provided in config - skipping")
            return
        try:
            with open(spelling_file, "r", encoding="utf-8") as f:
                self.load_words_from_file(f)

        except FileNotFoundError as e:
            recoverable_error("Failed to load spelling_file %s: %s" %
                              (spelling_file, e), self.config.bypass_errors,
                              error=e)


    def load_words_from_file(self, fhandle):
        """
        Read a file or file-like object line by line and add the words
        from that file to the built-in dictionary.
        """
        new_words = []
        for line in fhandle:
            word = line.strip().lower()
            if word:
                new_words.append(word)
        if new_words:
            self.spell.word_frequency.load_words(new_words)
            logger.info("Loaded %d words into the dictionary"%len(new_words))


    def check_all(self, only_page=None):
        """
        Reads all pages for this checker's target and checks them for style.

        Sets self.issues to an array of tuples with any recommended changes.
        """

        logger.info("Loading pages in target %s"%self.target.name)
        pages = self.target.load_pages()
        logger.info("Done loading pages.")

        context = {
            "current_time": time.strftime(self.config["time_format"]), # Get time once only
            "config": self.config,
            "mode": "html",
            "target": self.target.data,
            "pages": [p.data for p in pages], # just data, for legacy compat
            "categories": self.target.categories(),
        }

        logger.info("Style Checker - checking all pages in target %s"%self.target.name)

        self.reports = []
        for page in pages:
            if only_page and page.data["html"] != only_page:
                logger.debug("Only page mode - skipping %s"%page)
                continue
            pr = self.check_page(page, context)
            if pr is not None:
                logger.info(pr.describe_scores())
                logger.info(pr.report_page_length())
                self.reports.append(pr)
        return self.reports


    def check_page(self, page, context):
        logger.info("Checking page %s..." % page)
        page_context = {"currentpage":page.data, **context}
        page.html_content(page_context) # This defines page.soup
        logger.debug("page.soup is... %s"%page.soup)
        # If the page has no content, soup can be empty and that's OK.
        if not page.soup.find_all():
            logger.info("...page %s has no content."%page)
            return


        # There normally aren't any <div> tags in HTML made from Markdown, but
        # sometimes it's useful for Dactyl filters to wrap stuff in them. So
        # let's strip any of those out.
        [div.unwrap() for div in page.soup.find_all(name="div")]

        # Sometimes certain elements don't have whitespace between then, so
        # .get_text() will mash words together. Adding ". " makes them register
        # as separate sentences, which is probably more accurate for readability.
        might_need_space = page.soup.find_all(name=["li","th","td"])
        for tag in might_need_space:
            tag.append(" ")

        # All text in the parsed Markdown content should be contained in
        # one of these elements, except we ignore code samples.
        block_elements = ["p","blockquote","ul","table","h1","h2","h3","h4","h5","h6"]
        blocks = [el for el in page.soup.find_all(
                    name=block_elements, recursive=False)]


        page_text = ""
        page_misspellings = {}
        page_issues = []
        ignore_words = self.get_overrides(page.soup, use_regex=SPELLING_OVERRIDE_REGEX)
        logger.debug("Set of words to ignore for this file: %s"%ignore_words)
        if page.data.get("skip_spell_checker", False):
            logger.info("Skipping spell checker for page %s." % page)
        for block in blocks:
            overrides = self.get_overrides(block)
            # "Wipe" inlined <code> elements so we don't style-check
            # code samples.
            [code.clear() for code in block.find_all("code")]
            passage_text = block.get_text()
            logger.debug("passage text: %s"%passage_text)

            passage_issues = self.check_passage(passage_text, overrides)
            if passage_issues:
                page_issues += passage_issues

            if not page.data.get("skip_spell_checker", False):
                passage_misspellings = self.check_spelling(passage_text, ignore_words)
                if passage_misspellings:
                    page_misspellings.update(passage_misspellings)

            # Add this passage to the page text. Most readability scores seem
            # to handle lists/bullets/headings/etc. best if we treat them like
            # more sentences in an ongoing paragraph.
            if passage_text.strip():
                page_text += passage_text.strip()+". "

        # Readability formulas are only appropriate for paragraphs
        logger.debug("... Text for readability scoring:\n%s"%page_text)

        return style_report.PageReport(page, page_issues, page_misspellings, page_text)



    def report(self):
        """
        Print a report of discovered style issues to stdout.
        """
        if self.reports is None:
            self.check_all()

        num_pages = len(self.reports)
        sum_issues = sum([len(pr.issues) for pr in self.reports])
        sum_misspellings = sum([len(pr.misspellings) for pr in self.reports])
        avg_page = style_report.AveragePage(self.reports)

        if not num_pages:
            logger.warning("No pages checked.")
            return

        print("-------------")
        print("Spell Checker")
        print("-------------")
        if not sum_misspellings:
            print("No spelling mistakes found in %d pages!" % num_pages)
        else:
            print("Found %d possible spelling errors:" % sum_misspellings)
            for pr in self.reports:
                if pr.misspellings:
                    print(pr.report_spelling())


        print("-----------------------------")
        print("Discouraged Words and Phrases")
        print("-----------------------------")
        if not sum_issues:
            print("No discouraged words/phrases found in %d pages!" % num_pages)
        else:
            print("Found %d discouraged words/phrases:" % sum_issues)
            self.report_discouraged_words_phrases()


        print("------------------")
        print("Readability Scores")
        print("------------------")
        print(avg_page.describe_scores())
        print("")
        print("Most difficult pages by Flesch Reading Ease:")
        worst = sorted(self.reports,
                       key=lambda x:x.scores["flesch_reading_ease"]
                      )[:3]
        for pr in worst:
            print(pr.describe_scores())

        passed = sum([len(pr.goals_passed) for pr in self.reports])
        failed = sum([len(pr.goals_failed) for pr in self.reports])
        if passed+failed:
            print("------------------")
            print("Readability Goals:")
            print("------------------")
            print("{passed} passed out of {total} total goals ({pct:.1%})".format(
                passed=passed,total=passed+failed,pct=passed/(passed+failed)
            ))
            if failed:
                print("")
                print("Failing pages:")
                for pr in self.reports:
                    if pr.goals_failed:
                        print("{} ({})".format(pr.page, ", ".join(pr.goals_failed)))

        print("-------------------")
        print("Page Length Metrics")
        print("-------------------")
        print(avg_page.report_page_length())

        print("Longest pages by character count:")
        page_len_list = sorted(self.reports,
                       key=lambda x:x.len_chars,
                       reverse=True
                      )
        for pr in page_len_list[:3]:
            print(pr.report_page_length())
        print("Shortest pages by character count:")
        for pr in page_len_list[-3:]:
            print(pr.report_page_length())



    def report_discouraged_words_phrases(self):
        # for pagename,issuelist in self.issues:
        for pr in self.reports:
            if not pr.issues:
                continue
            print("Page: %s" % pr.page)
            c = collections.Counter(pr.issues)
            for i, count_i in c.items():
                if i[0]=="Unplain Phrase":
                    print("   Discouraged phrase: %s (%d instances); suggest '%s' instead." %
                                    ( i[1], count_i, self.disallowed_phrases[i[1].lower()] ))
                elif i[0]=="Unplain Word":
                    print("   Discouraged word: %s (%d instances); suggest '%s' instead." %
                                    ( i[1], count_i, self.disallowed_words[i[1].lower()] ))
                else:
                    print("   %s: %s (%d instances)" % (i[0], i[1], count_i))


    def get_overrides(self, soup, use_regex=OVERRIDE_COMMENT_REGEX):
        """
        Look for overrides in the text to make exceptions for specific style
        rules. Returns a set of rule strings to ignore for this block.
        """

        overrides = set()
        comments = soup.find_all(string=lambda text:isinstance(text,Comment))
        for comment in comments:
            m = re.match(use_regex, comment)
            if m:
                new_overrides = m.group(1).split(",")
                new_overrides = {o.strip() for o in new_overrides}
                if use_regex == SPELLING_OVERRIDE_REGEX:
                    new_overrides = {o.lower() for o in new_overrides}
                logger.info("Overrides found: %s" % new_overrides)
                overrides |= new_overrides

        return overrides

    def check_passage(self, passage, overrides):
        """Checks an individual string of text for style issues."""
        issues = []
        logging.debug("Checking passage %s" % passage)
        tokens = self.tokenize(passage)
        for t in tokens:
            if t.lower() in self.disallowed_words:
                if t.lower() in overrides:
                    logger.info("Unplain word violation %s overridden" % t)
                    continue
                issues.append( ("Unplain Word", t.lower()) )

        for phrase,sub in self.disallowed_phrases.items():
            if phrase.lower() in self.depunctuate(passage):
                if phrase.lower() in overrides:
                    logger.info("Unplain phrase violation %s overridden" % t)
                    continue
                issues.append( ("Unplain Phrase", phrase.lower()) )

        return issues

    def check_spelling(self, passage, ignore_words=set()):
        """Checks a string of text for spelling mistakes."""

        logging.debug("Spell-checking passage: <<<%s>>>" % passage)
        tokens = [t.lower() for t in self.tokenize(passage)]

        unknown = self.spell.unknown(tokens) - ignore_words
        if unknown:
            logger.info("Unknown/misspelled words: %s"%unknown)

        return {w: list(self.spell.candidates(w)-{w})[:3] for w in unknown}




def main(cli_args, config):
    target = DactylTarget(config, name=cli_args.target)
    checker = DactylStyleChecker(target, config)

    if cli_args.only:
        issues = checker.check_all(only_page=cli_args.only)
    else:
        issues = checker.check_all()
    checker.report()

    if [pr for pr in issues if not pr.passed]:
        exit(1)
    else:
        exit(0)


def dispatch_main():
    cli = DactylCLIParser(DactylCLIParser.UTIL_STYLE)
    config = DactylConfig(cli.cli_args)
    main(cli.cli_args, config)


if __name__ == "__main__":
    dispatch_main()
