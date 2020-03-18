################################################################################
## Callouts filter                                                            ##
## Author: Rome Reginelli                                                     ##
## Copyright: Ripple Labs, Inc. 2016                                          ##
##                                                                            ##
## Looks for sections starting **Note:** or **Caution:** and gives them CSS   ##
## classes like "callout note" so they can be styled accordingly.             ##
################################################################################
import re

CALLOUT_TYPES_FIELD = "callout_types"
CALLOUT_CLASS_FIELD = "callout_class"

DEFAULT_CALLOUT_TYPES = [
    "note",
    "warning",
    "tip",
    "caution"
]
DEFAULT_CALLOUT_CLASS = "dactyl-callout"

def filter_soup(soup, currentpage={}, config={}, **kwargs):
    """
    Find patterns that look like callouts, for example **Note:**, and add
    callout classes to their parent elements (usually <p>)
    """
    # callout classes are defined by page>target>config>default
    callout_classes = currentpage.get(CALLOUT_TYPES_FIELD,
                        config.get(CALLOUT_TYPES_FIELD,
                        DEFAULT_CALLOUT_TYPES))
    callout_intro = re.compile(r"("+"|".join(callout_classes)+"):?$", re.I)
    callout_base_class = currentpage.get(CALLOUT_CLASS_FIELD,
                        config.get(CALLOUT_CLASS_FIELD,
                        DEFAULT_CALLOUT_CLASS))

    callouts = soup.find_all(name=["strong","em"], string=callout_intro)
    for c in callouts:
        if not c.previous_sibling: #This callout starts a block
            callout_type = c.string.replace(":","").lower()
            if callout_type in callout_classes:
                c.parent["class"] = [callout_base_class, callout_type]
