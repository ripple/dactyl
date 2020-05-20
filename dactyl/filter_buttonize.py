################################################################################
## Buttonize links (Bootstrap-friendly edition)                               ##
## Author: Rome Reginelli                                                     ##
## Copyright: Ripple Labs, Inc. 2016–2020                                     ##
##                                                                            ##
## Looks for links ending in >, and adds Bootstrap button classes to those    ##
## links so they can be styled like buttons in the page.                      ##
################################################################################
import re

def filter_soup(soup, **kwargs):
    """make links ending in > render like buttons"""
    buttonlinks = soup.find_all("a", string=re.compile(">$"))
    for link in buttonlinks:
        link.string=link.string[:-1].strip()
        if "class" in link.attrs:
            link["class"].append("btn btn-primary")
        else:
            link["class"] = ["btn","btn-primary"]
