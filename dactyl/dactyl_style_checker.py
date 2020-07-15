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

from dactyl.dactyl_build import DactylBuilder
from dactyl.config import DactylConfig
from dactyl.cli import DactylCLIParser
from dactyl.target import DactylTarget
import dactyl.style_report as style_report

OVERRIDE_COMMENT_REGEX = r" *STYLE_OVERRIDE: *([\w, -]+)"




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

    @staticmethod
    def tokenize(passage):
        words = re.split(r"[\s,.;()!'\"]+", passage)
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
                self.reports.append(pr)


    def check_page(self, page, context):
        logger.info("Checking page %s..." % page)
        page_context = {"currentpage":page.data, **context}
        page.html_content(page_context) # This defines page.soup
        logger.debug("page.soup is... %s"%page.soup)
        # If the page has no content, soup can be empty and that's OK.
        if not page.soup.find_all():
            logger.warning("...page %s has no content."%page)
            return

        page_issues = []
        # All text in the parsed Markdown content should be contained in
        # one of these top-level elements, except we ignore code samples.
        block_elements = ["p","ul","table","h1","h2","h3","h4","h5","h6"]
        blocks = [el for el in page.soup.find_all(
                    name=block_elements, recursive=False)]


        page_text = ""
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

            # Add this passage to the page text. Most readability scores seem
            # to handle lists/bullets/headings/etc. best if we treat them like
            # more sentences in an ongoing paragraph.
            page_text += passage_text.strip()+". "

        # Readability formulas are only appropriate for paragraphs
        logger.debug("... Text for readability scoring:\n%s"%page_text)

        return style_report.PageReport(page, page_issues, page_text)



    def report(self):
        """
        Print a report of discovered style issues to stdout.
        """
        if self.reports is None:
            self.check_all()

        num_pages = len(self.reports)
        sum_issues = sum([len(pr.issues) for pr in self.reports])

        if not num_pages:
            logger.warning("No pages checked.")
            return

        print("-----------------------------")
        print("Discouraged Words and Phrases")
        print("-----------------------------")
        if not sum_issues:
            print("No discouraged words/phrases found in %d pages!" % num_pages)
        else:
            print("Found %d discouraged words/phrases:" % sum_issues)
            self.report_discouraged_words_phrases()


        print("----------------------------------")
        print(style_report.AveragePage(self.reports).describe_scores())
        print("")
        print("Most difficult pages by Flesch Reading Ease:")
        worst = sorted(self.reports,
                       key=lambda x:x.scores["flesch_reading_ease"]
                      )[:3]
        for pr in worst:
            print(pr.describe_scores())
        print("----------------------------------")

        passed = sum([len(pr.goals_passed) for pr in self.reports])
        failed = sum([len(pr.goals_failed) for pr in self.reports])
        if passed+failed:
            print("----------------------------------")
            print("Readability Goals:")
            print("{passed} passed out of {total} total goals ({pct:.1%})".format(
                passed=passed,total=passed+failed,pct=passed/(passed+failed)
            ))
            if failed:
                print("")
                print("Failing pages:")
                for pr in self.reports:
                    if pr.goals_failed:
                        print("{} ({})".format(pr.page, ", ".join(pr.goals_failed)))
            print("----------------------------------")


    def report_discouraged_words_phrases(self):
        # for pagename,issuelist in self.issues:
        for pr in self.reports:
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


    def get_overrides(self, soup):
        """
        Look for overrides in the text to make exceptions for specific style
        rules. Returns a set of rule strings to ignore for this block.
        """

        overrides = set()
        comments = soup.find_all(string=lambda text:isinstance(text,Comment))
        for comment in comments:
            m = re.match(OVERRIDE_COMMENT_REGEX, comment)
            if m:
                new_overrides = m.group(1).split(",")
                new_overrides = {o.strip() for o in new_overrides}
                logger.info("Overrides found: %s" % new_overrides)
                overrides |= new_overrides

        return overrides

    def check_passage(self, passage, overrides):
        """Checks an individual string of text for style issues."""
        issues = []
        logging.debug("Checking passage %s" % passage)
        #tokens = nltk.word_tokenize(passage)
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




def main(cli_args, config):
    target = DactylTarget(config, name=cli_args.target)
    checker = DactylStyleChecker(target, config)

    if cli_args.only:
        issues = checker.check_all(only_page=cli_args.only)
    else:
        issues = checker.check_all()
    checker.report()
    if issues:
        exit(1)
    else:
        exit(0)


def dispatch_main():
    cli = DactylCLIParser(DactylCLIParser.UTIL_STYLE)
    config = DactylConfig(cli.cli_args)
    main(cli.cli_args, config)


if __name__ == "__main__":
    dispatch_main()
