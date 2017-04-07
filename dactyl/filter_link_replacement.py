################################################################################
## Substitute Links filter                                                    ##
## Author: Rome Reginelli                                                     ##
## Copyright: Ripple Labs, Inc. 2017                                          ##
##                                                                            ##
## Replaces the link substitution feature built into Dactyl < 0.4.0 with a    ##
## filter to do about the same.                                               ##
################################################################################

import re

LINK_SUBS_FIELD = "link_subs"
LINK_RE_SUBS_FIELD = "link_re_subs"
PARAMETER_REPLACE_FIELD = "replace_parameter_links"
IMAGE_SUBS_FIELD = "image_subs"
IMAGE_RE_SUBS_FIELD = "image_re_subs"
IMAGE_LINK_REGEX = re.compile(r"^[^.]+\.(png|jpg|jpeg|gif|svg)", re.I)

def filter_soup(soup, currentpage={}, target={}, pages=[], logger=None, **kwargs):
    """
    Replaces links and image hrefs in the current page, based on a substitution
    map in the target or page settings. Also looks into values in the current
    page's metadata and replaces links there, in case the template uses fields
    from the current page's metadata key/values.
    """
    globals()["logger"] = logger
    # currentpage already includes link subs inherited from the target
    if LINK_SUBS_FIELD in currentpage:
        link_subs = currentpage[LINK_SUBS_FIELD]

        if (PARAMETER_REPLACE_FIELD in currentpage and
                currentpage[PARAMETER_REPLACE_FIELD]):
            substitute_parameter_links(currentpage, link_subs)
        substitute_links(soup, link_subs)

    if LINK_RE_SUBS_FIELD in currentpage:
        link_re_subs = currentpage[LINK_RE_SUBS_FIELD]
        re_sub_links(soup, link_re_subs)

    if IMAGE_SUBS_FIELD in currentpage:
        image_subs = currentpage[IMAGE_SUBS_FIELD]
        substitute_images(soup, image_subs)
        substitute_links(soup, image_subs)

    if IMAGE_RE_SUBS_FIELD in currentpage:
        image_re_subs = currentpage[IMAGE_RE_SUBS_FIELD]
        re_sub_images(soup, image_re_subs)
        re_sub_links(soup, image_re_subs)

def substitute_links(soup, link_subs):
    """
    Takes a map of needle:replacement strings and changes the href values of
    <a> tags in the soup, so that any that start with the needle are changed to
    start with the replacement instead (preserving the remainder).
    """
    links = soup.find_all("a", href=True)
    for link in links:
        for needle, replacement in link_subs.items():
            if link["href"][:len(needle)] == needle:
                new_href = replacement + link["href"][len(needle):]
                logger.info("... replacing link '%s' with '%s'" %
                            (link["href"], new_href) )
                link["href"] = new_href

def substitute_images(soup, image_subs):
    """
    Takes a map of needle:replacement strings and changes the src of <img>
    tags in the soup so that any that match the needle are changed to use the
    replacement instead.
    """
    images = soup.find_all("img")
    for img in images:
        for needle, replacement in image_subs.items():
            if needle == img["src"]:
                logger.info("... replacing image '%s' with '%s'" %
                            (img["src"], replacement) )
                img["src"] = replacement


def re_sub_images(soup, image_re_subs):
    """
    Takes a map of regular expressions to regular-expression replacements and
    changes the src of any <img> tags in the soup by doing regular-expression
    match/replace.
    """
    images = soup.find_all("img", src=True)
    for img in images:
        for regex,replace_pattern in image_re_subs.items():
            m = re.match(regex, img["src"])
            if m:
                new_path = re.sub(regex, replace_pattern, img["src"])
                logger.info("... replacing image '%s' with '%s'" %
                            (img["src"], new_path) )
                img["src"] = new_path

def re_sub_links(soup, link_re_subs):
    """
    Takes a map of regular expressions to regular-expression replacements and
    changes the href of any <a> tags in the soup by doing regular-expression
    match/replace.
    """
    links = soup.find_all("a", href=True)
    for link in links:
        for regex,replace_pattern in link_re_subs.items():
            m = re.match(regex, link["href"])
            if m:
                new_path = re.sub(regex, replace_pattern, link["href"])
                logger.info("... replacing link '%s' with '%s'" %
                            (link["href"], new_path) )
                link["href"] = new_path

RESERVED_PAGE_KEYS = [
    "html",
    "md",
    "category",
    "targets"
]
def substitute_parameter_links(currentpage, link_subs):
    """
    Takes a map of needle:replacement link substitutions and applies them to
    string values in the current page's metadata parameters.
    """
    for field,val in currentpage.items():
        if field in RESERVED_PAGE_KEYS:
            continue;
        if type(val) != str:
            continue
        for needle, replacement in link_subs:
            if val[:len(needle)] == needle:
                new_val = replacement + val[len(needle):]
                logger.info(("... replacing field '%s'; replacing value "+
                            "'%s' with '%s'") %  (field, val, new_val) )
                currentpage[field] = new_val

class MDLink: # Used for link substitution on markdown
    """A markdown link, in one of the following formats:
    - [label](url "title") — an inline link (title optional)
    - ![alt text](url) — an inline image link
    - [ref]: url — a reference link definition (could be an image or not)


    Affects, but does not include, reference link instances, such as:
    - [ref][]
    - [label][ref]
    """

    MD_LINK_REGEX = re.compile(
        r"(\[([^\]]+)\]\(([^:)]+)\)|\[([^\]]+)\]:\s*(\S+)$)", re.MULTILINE)

    MD_IMG_REGEX = re.compile(
        r"!(\[([^\]]+)\]\(([^:)]+)\)|\[([^\]]+)\]:\s*(\S+)$)", re.MULTILINE)

    def __init__(self, fullmatch, label, url, label2, url2):
        self.fullmatch = fullmatch
        if fullmatch[:1] == "!":
            self.is_img = True
        else:
            self.is_img = False
        if label:
            self.label = label
            self.url = url
            self.is_reflink = False
        elif label2:
            self.label = label2
            self.url = url2
            self.is_reflink = True

    def to_markdown(self):
        """Re-represent self as a link in markdown syntax"""
        s = "[" + self.label + "]"
        if self.is_reflink:
            s += ": " + self.url
        else:
            s += "(" + self.url + ")"
        return s

def filter_markdown(md, mode="html", currentpage={}, **kwargs):
    """
    In "Githubify" mode, we need to do link substitution on the Markdown itself
    since we won't have an opportunity to do it on the HTML output.
    """
    if mode != "md":
        return md

    if LINK_SUBS_FIELD in currentpage:
        link_subs = currentpage[LINK_SUBS_FIELD]
        md = substitute_md_links(md, link_subs)

    if IMAGE_SUBS_FIELD in currentpage:
        image_subs = currentpage[IMAGE_SUBS_FIELD]
        md = substitute_md_images(currentpage, image_subs)
        md = substitute_md_links(currentpage, image_subs)

    return md

def substitute_md_links(md, link_subs, do_images=False):
    if do_images:
        regex = MDLink.MARKDOWN_LINK_REGEX
    else:
        regex = MDLink.MARKDOWN_IMG_REGEX
    links = [MDLink(*m) for m in regex.findall(md)]

    for link in links:
        for needle, replacement in link_subs:
            if link.url[:len(needle)] == needle:
                link.url = replacement + link.url[len(needle):]
                md = md.replace(link.fullmatch, link.to_markdown())

    return md

def substitute_md_images(md, image_subs):
    return substitute_md_links(md, image_subs, do_images=True)
