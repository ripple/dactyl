################################################################################
# Dactyl common code
#
# Imports and utilities shared across multiple pieces of Dactyl
################################################################################

# The ElasticSearch templates need to write *actual* JSON and not YAML
import json
import logging
import os
import re
import time
import traceback

import ruamel.yaml
yaml = ruamel.yaml.YAML(typ="safe")

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

DEFAULT_PDF_FILE = "__DEFAULT_FILENAME__"
NO_PDF = "__NO_PDF__"
DEFAULT_ES_URL = "__DEFAULT_ES_HOST__"
NO_ES_UP = "__NO_ES_UP__"

def recoverable_error(msg, bypass_errors):
    """Logs a warning/error message and exits if bypass_errors==False"""
    logger.error(msg)
    if not bypass_errors:
        exit(1)

# Note: this regex means non-ascii characters get stripped from filenames,
#  which is not preferable when making non-English filenames.
unacceptable_chars = re.compile(r"[^A-Za-z0-9._ ]+")
whitespace_regex = re.compile(r"\s+")
def slugify(s):
    s = re.sub(unacceptable_chars, "", s)
    s = re.sub(whitespace_regex, "_", s)
    if not s:
        s = "_"
    return s

def guess_title_from_md_file(filepath):
    """Takes the path to an md file and return a suitable title.
    If the first two lines look like a Markdown header, use that.
    Otherwise, return the filename."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            line1 = f.readline()
            line2 = f.readline()

            # look for headers in the "followed by ----- or ===== format"
            ALT_HEADER_REGEX = re.compile("^[=-]{3,}$")
            if ALT_HEADER_REGEX.match(line2):
                possible_header = line1
                if possible_header.strip():
                    return possible_header.strip()

            # look for headers in the "## abc ## format"
            HEADER_REGEX = re.compile("^#+\s*(.+[^#\s])\s*#*$")
            m = HEADER_REGEX.match(line1)
            if m:
                possible_header = m.group(1)
                if possible_header.strip():
                    return possible_header.strip()
    except FileNotFoundError as e:
        logger.warning("Couldn't guess title of page (file not found): %s" % e)

    #basically if the first line's not a markdown header, we give up and use
    # the filename instead
    return os.path.basename(filepath)

def parse_frontmatter(text):
    """Separate YAML frontmatter, if any, from a string, and return the
    text separate from the parsed front-matter."""
    if len(text) < 6:
        logger.debug("...too short for frontmatter")
        return text, {}

    if text[:3] == "---" and text.find("---", 3) != -1:
        logger.debug("...has front matter")
        raw_frontmatter = text[3:text.find("---", 3)]
        frontmatter = yaml.load(raw_frontmatter)
        # Map some Jekyll-specific frontmatter variables to their Dactyl equivs
        if "title" in frontmatter.keys():
            # We don't care about the Jekyll "page.name" field so it's OK to
            #   overwrite it.
            frontmatter["name"] = frontmatter["title"]
        if "categories" in frontmatter.keys() and len(frontmatter["categories"]):
            frontmatter["category"] = frontmatter["categories"][0]
        print("Loaded frontmatter:", frontmatter)#TODO: remove me

        return text[text.find("---", 3)+4:], frontmatter
    else:
        logger.debug("...no front matter detected")
        return text, {}
