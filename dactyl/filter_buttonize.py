################################################################################
## Buttonize links                                                            ##
## Author: Rome Reginelli                                                     ##
## Copyright: Ripple Labs, Inc. 2016-2021                                     ##
##                                                                            ##
## Looks for links ending in >, and adds a "btn btn-primary" classes to those ##
## links so, they get styled like buttons.                                    ##
################################################################################
import re

def filter_soup(soup, logger=None, **kwargs):
    """make links ending in > render like buttons"""
    buttonlinks = soup.find_all("a", string=re.compile("(&gt;|>)$"))
    # logger.debug(f"Button links found: {buttonlinks}")
    for link in buttonlinks:
        link.string=link.string[:-1].strip()

        oldclass = link.get('class',[])
        if type(oldclass) == str:
            oldclass = [oldclass]
        link['class'] = oldclass + ['btn', 'btn-primary']
