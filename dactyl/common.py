import logging
import os
import re
import time
import traceback
import yaml

logger = logging.getLogger(__name__)

def recoverable_error(msg, bypass_errors):
    """Logs a warning/error message and exits if bypass_errors==False"""
    logger.error(msg)
    if not bypass_errors:
        exit(1)


def guess_title_from_md_file(filepath):
    """Takes the path to an md file and return a suitable title.
    If the first two lines look like a Markdown header, use that.
    Otherwise, return the filename."""
    with open(filepath, "r") as f:
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

    #basically if the first line's not a markdown header, we give up and use
    # the filename instead
    return os.path.basename(filepath)
