################################################################################
## Dactyl Page Class
##
## Handles readability scores and some other details of page style reporting.
################################################################################

import textstat

from dactyl.common import *
from dactyl.page import DactylPage

def grade_level_desc(score):
    return "Grade level {score:.1f}".format(score=score)

DALE_CHALL_RATINGS = {
    10.0: "higher than average college level",
    9.0: "average college student",
    8.0: "average 11th or 12-grade student",
    7.0: "average 9th or 10th-grade student",
    6.0: "average 7th or 8th-grade student",
    5.0: "average 5th or 6th-grade student",
    0: "average 4th-grade student or lower"
}
def dale_chall_desc(score):
    """
    Return a text rating for a given Dale-Chall Readability Score
    """

    for key in sorted(DALE_CHALL_RATINGS.keys(), reverse=True):
        if score >= key:
            desc = DALE_CHALL_RATINGS[key]
            break
    else:
        desc = DALE_CHALL_RATINGS[0]
    return "{score:.1f} ({desc})".format(score=score, desc=desc)

FRE_RATINGS = {
    90: "Very Easy", # any score 90 or higher; max is 121.22
    80: "Easy",
    70: "Fairly Easy",
    60: "Standard",
    50: "Fairly Difficult",
    30: "Difficult",
    0: "Very Confusing" # technically applies to negative scores too
}
def fre_desc(score):
    """
    Return a text rating for a given Flesch Readability Score
    """

    for key in sorted(FRE_RATINGS.keys(), reverse=True):
        if score >= key:
            desc = FRE_RATINGS[key]
            break
    else:
        desc = FRE_RATINGS[0]
    return "{score:.1f} ({desc})".format(score=score,desc=desc)


TESTS = {
    # keys are the textstat module method names and also yaml keys
    # Defaults:
    # - higher_is_better: False
    # - desc function: grade_level_desc
    "flesch_reading_ease": {
        "name": "Flesch Reading Ease Score",
        "higher_is_better": True,
        "desc": fre_desc
    },
    "dale_chall_readability_score": {
        "name": "Dale-Chall Readability Score",
        "desc": dale_chall_desc
    },
    "smog_index": {"name": "SMOG Index"},
    "gunning_fog": {"name": "Gunning FOG Index"},
    "automated_readability_index": {"name": "Automated Readability Index"},
    "coleman_liau_index": {"name": "Coleman-Liau Index"},
    "linsear_write_formula": {"name": "Linsear Write Formula"},
}


class PageReport:
    def __init__(self, page, issues, misspellings, page_text):
        self.page = page
        self.issues = issues
        self.misspellings = misspellings
        self.scores = self.get_scores(page_text)
        self.page_length(page_text)
        self.goals_passed, self.goals_failed = self.readability_goals()

    def get_scores(self, page_text):
        scores = {}
        for test in TESTS.keys():
            scores[test] = getattr(textstat, test)(page_text)
        return scores

    def describe_scores(self):
        """
        Returns a string that helps interpret the readability scores
        """

        s = "%s Readability Scores:\n" % self.page

        for test, deets in TESTS.items():
            descfunc = deets.get("desc", grade_level_desc)
            s += "  {testname}: {desc}\n".format(
                testname = deets["name"],
                desc = descfunc(self.scores[test])
            )

        return s

    def page_length(self, page_text):
        """
        Calculate page length metrics
        """
        self.len_chars = len(page_text)
        self.len_words = len( re.split(r'\w+', page_text))
        self.len_sentences = len( re.split(r'[.?!][)"]?\s', page_text) )

    def report_page_length(self):
        """
        Returns a string that indicates the page length details
        """

        s = "%s Length Metrics:\n" % self.page
        s += "  Sentences: {:,.0f}\n".format(self.len_sentences)
        s += "  Words: {:,.0f}\n".format(self.len_words)
        s += "  Characters: {:,.0f}\n".format(self.len_chars)

        return s

    def report_spelling(self):
        """
        Returns a string with spell-checker errors and suggested replacements.
        """
        if not self.misspellings:
            return "%s passed spelling check." % self.page

        s = "%s Unknown Words:\n" % self.page
        for nonword, suggestions in self.misspellings.items():
            s += "  {nonword}: {suggestions}\n".format(
                nonword=nonword,
                suggestions = ", ".join(suggestions)
            )

        return s

    def readability_goals(self):
        """
        Returns two lists with the goals this page passed and the ones it failed
        where 'passed' means it scored better than the goal for the page.
        To have a goal, the page must have a readability_goals field, which has
        at least one test name and target value. To pass its goals, the page
        must score equal or better (easier to read) than the target value.
        """
        if not isinstance(self.page, DactylPage):
            logger.debug("readability_goals(): not a DactylPage: %s"%self.page)
            return [],[]

        failed_goals = []
        passed_goals = []
        goals = self.page.data.get("readability_goals", {})

        for test,deets in TESTS.items():
            if test not in goals:
                continue

            higher_is_better = deets.get("higher_is_better", False)

            if (higher_is_better and self.scores[test] >= goals[test]) or \
               (not higher_is_better and self.scores[test] <= goals[test]):

                passed_goals.append(test)
                logger.info("{} passed {} test ({} vs goal of {})".format(
                    self.page, deets["name"], self.scores[test], goals[test]
                ))

            else:
                failed_goals.append(deets["name"])

        return passed_goals,failed_goals

class AveragePage(PageReport):
    def __init__(self, reports):
        """
        reports should be a list of PageReport objects to average
        """
        self.page = "Average Page"
        num_pages = len(reports)

        if not num_pages:
            self.scores = {test: 0 for test in TESTS.keys()}
            self.len_chars = 0
            self.len_words = 0
            self.len_sentences = 0
            return

        self.scores = {test: sum([pg.scores[test] for pg in reports])/num_pages
            for test in TESTS.keys()
        }

        self.len_chars = sum([pg.len_chars for pg in reports])/num_pages
        self.len_words = sum([pg.len_words for pg in reports])/num_pages
        self.len_sentences = sum([pg.len_sentences for pg in reports])/num_pages
