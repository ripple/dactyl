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

from pkg_resources import resource_stream

import ruamel.yaml
yaml = ruamel.yaml.YAML(typ="safe")

import gettext

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.propagate = False

PDF_USE_DEFAULT = "__DEFAULT_FILENAME__"
NO_PDF = "__NO_PDF__"
ES_USE_DEFAULT = "__ES_USE_DEFAULT__"
NO_ES_UP = False

# These fields are special, and pages don't inherit them directly
RESERVED_KEYS_TARGET = [
    "name",
    "display_name",
    "pages",
]
ADHOC_TARGET = "__ADHOC__"
UNTITLED_TARGET = "(Untitled)"

PROVIDED_FILENAME_KEY = "__dactyl_provided_filename__"
ES_EVAL_KEY = "__dactyl_eval__"
OPENAPI_SPEC_KEY = "openapi_specification"
OPENAPI_TEMPLATE_PATH_KEY = "openapi_md_template_path"
OPENAPI_SPEC_PLACEHOLDER = "__OPENAPI_SPEC_PLACEHOLDER__"
NOT_LOADED_PLACEHOLDER = "__NOT_LOADED_PLACEHOLDER__"
API_SLUG_KEY = "api_slug"
BUILTIN_ES_TEMPLATE = "templates/template-es.json"

DEFAULT_SERVER_PORT = 32289 # "DACTY" in T-9


def recoverable_error(msg, bypass_errors, error=None):
    """Logs a warning/error message and exits if bypass_errors==False"""
    if not bypass_errors and error is not None:
        traceback.print_tb(error.__traceback__)
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
        logger.debug("Loaded frontmatter: %s"% frontmatter)

        return text[text.find("---", 3)+4:], frontmatter
    else:
        logger.debug("...no front matter detected")
        return text, {}

def merge_dicts(default_d, specific_d, reserved_keys_top=[]):
    """
    Extend specific_d with values from default_d (recursively), keeping values
    from specific_d where they both exist. (This is like dict.update() but
    without overwriting duplicate keys in the updated dict.)

    reserved_keys_top is only used at the top level, not recursively
    """
    for key,val in default_d.items():
        if key in reserved_keys_top:
            continue
        if key not in specific_d.keys():
            specific_d[key] = val
        elif type(specific_d[key]) == dict and type(val) == dict:
                merge_dicts(val, specific_d[key])
        #else leave the key in the specific_d
