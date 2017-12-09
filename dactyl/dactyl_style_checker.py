#!/usr/bin/env python3

###############################################################################
## Dactyl Style Police                                                       ##
## Author: Rome Reginelli                                                    ##
## Copyright: Ripple Labs, Inc. 2016                                         ##
##                                                                           ##
## Reads the markdown files to try and enforce elements of good style.       ##
###############################################################################

from dactyl.common import *

#import nltk
import collections

from bs4 import BeautifulSoup
from bs4 import Comment
from bs4 import NavigableString

from dactyl import dactyl_build
from dactyl.config import DactylConfig
from dactyl.cli import DactylCLIParser

OVERRIDE_COMMENT_REGEX = r" *STYLE_OVERRIDE: *([\w, -]+)"

def tokenize(passage):
    words = re.split(r"[\s,.;()!'\"]+", passage)
    return [w for w in words if w]

def depunctuate(passage):
    punctuation = re.compile(r"[,.;()!'\"]")
    return re.sub(punctuation, "", passage)

def check_all_pages(target=None):
    """Reads all pages for a target and checks them for style."""
    target = dactyl_build.get_target(target)
    pages = dactyl_build.get_pages(target)

    pp_env = dactyl_build.setup_pp_env()

    print("Style Checker - checking all pages in target %s" % target["name"])

    style_issues = []
    for page in pages:
        if "md" not in page:
            # Not a doc page, move on
            continue
        logger.info("Checking page %s" % page["name"])
        page_issues = []
        html = dactyl_build.parse_markdown(page, pages=pages, target=target)
        soup = BeautifulSoup(html, "html.parser")

        overrides = get_overrides(soup)

        content_elements = ["p","li","a","em","strong","th","td",
                            "h1","h2","h3","h4","h5","h6"]
        for el in soup.descendants:
            if (type(el) == NavigableString and
                el.parent.name in content_elements and
                str(el).strip()):
                passage = str(el).strip()
                passage_issues = check_passage(passage, overrides)
                if passage_issues:
                    page_issues += passage_issues
                #print("'%s' (%s)" % (el, el.parent.name))
        # for el in soup.find_all(content_elements):
        #     for passage in el.stripped_strings:
        #         passage_issues = check_passage(passage, overrides)
        #         if passage_issues:
        #             page_issues += passage_issues

        if page_issues:
            style_issues.append( (page["name"], page_issues) )

    return style_issues

def get_overrides(soup):
    overrides = []
    comments = soup.find_all(string=lambda text:isinstance(text,Comment))
    for comment in comments:
        m = re.match(OVERRIDE_COMMENT_REGEX, comment)
        if m:
            new_overrides = m.group(1).split(",")
            new_overrides = [o.strip() for o in new_overrides]
            logger.info("Overrides found: %s" % new_overrides)
            overrides += new_overrides
    return overrides

def check_passage(passage, overrides):
    """Checks an individual string of text for style issues."""
    issues = []
    logging.debug("Checking passage %s" % passage)
    #tokens = nltk.word_tokenize(passage)
    tokens = tokenize(passage)
    for t in tokens:
        if t.lower() in config["disallowed_words"]:
            if t.lower() in overrides:
                logger.info("Unplain word violation %s overridden" % t)
                continue
            issues.append( ("Unplain Word", t.lower()) )

    for phrase,sub in config["disallowed_phrases"].items():
        if phrase.lower() in depunctuate(passage):
            if phrase.lower() in overrides:
                logger.info("Unplain phrase violation %s overridden" % t)
                continue
            #logging.warn("Unplain phrase: %s; suggest %s instead" % (phrase, sub))
            issues.append( ("Unplain Phrase", phrase.lower()) )

    return issues

def main(cli_args):
    if len(config["targets"]) == 0:
        exit("No target found; maybe you need to specify a Dactyl config file?")

    issues = check_all_pages(target=cli_args.target)
    if issues:
        num_issues = sum(len(p[1]) for p in issues)
        print("Found %d issues:" % num_issues)
        for pagename,issuelist in issues:
            print("Page: %s" % pagename)
            c = collections.Counter(issuelist)
            for i, count_i in c.items():
                if i[0]=="Unplain Phrase":
                    print("   Discouraged phrase: %s (%d instances); suggest '%s' instead." %
                                    ( i[1], count_i, config["disallowed_phrases"][i[1].lower()] ))
                elif i[0]=="Unplain Word":
                    print("   Discouraged word: %s (%d instances); suggest '%s' instead." %
                                    ( i[1], count_i, config["disallowed_words"][i[1].lower()] ))
                else:
                    print("   %s: %s (%d instances)" % (i[0], i[1], count_i))
        exit(1)
    else:
        print("Style check passed with flying colors!")
        exit(0)


def dispatch_main():
    cli = DactylCLIParser(DactylCLIParser.UTIL_STYLE)
    global config
    config = DactylConfig(cli.cli_args)
    config.load_style_rules()
    dactyl_build.config = config # consider fixing this hack with a refactor
    main(cli.cli_args)


if __name__ == "__main__":
    dispatch_main()
