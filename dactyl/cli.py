#!/usr/bin/env python3
from dactyl.common import *
import argparse

class DactylCLIParser:
    UTIL_BUILD = "Generate static site from markdown and templates."
    UTIL_LINKS = "Check files in this repository for broken links."
    UTIL_STYLE = "Check content files for style issues."

    def __init__(self, utility):
        """Specify commandline usage and parse arguments"""
        parser = argparse.ArgumentParser(description=utility)

        noisiness = parser.add_mutually_exclusive_group(required=False)
        noisiness.add_argument("--quiet", "-q", action="store_true",
                            help="Suppress status messages")
        noisiness.add_argument("--debug", action="store_true",
                            help="Print debug-level log messages")

        parser.add_argument("--config", "-c", type=str,
                            help="Specify path to an alternate config file.")
        parser.add_argument("--version", "-v", action="store_true",
                            help="Print version information and exit.")
        parser.add_argument("--bypass_errors", "-b", action="store_true",
                            help="Continue if recoverable errors occur")

        if utility in (self.UTIL_BUILD, self.UTIL_STYLE):
            parser.add_argument("--target", "-t", type=str,
                help="Use the specified target (from the config file).")

        if utility == self.UTIL_BUILD:
            build_mode = parser.add_mutually_exclusive_group(required=False)
            build_mode.add_argument("--pdf", nargs="?", type=str,
                                const=DEFAULT_PDF_FILE, default=NO_PDF,
                                help="Output a PDF to this file. Requires Prince.")
            build_mode.add_argument("--md", action="store_true",
                                help="Output markdown only")
            # HTML is the default mode

            parser.add_argument("--copy_static", "-s", action="store_true",
                                help="Copy static files to the out dir",
                                default=False)
            parser.add_argument("--leave_temp_files", action="store_true",
                                help="Leave temp files in place (for debugging or "+
                                "manual PDF generation). Ignored when using --watch",
                                default=False)
            parser.add_argument("--list_targets_only", "-l", action="store_true",
                                help="Don't build anything, just display list of "+
                                "known targets from the config file.")
            parser.add_argument("--only", type=str, help=".md or .html filename of a "+
                                "single page in the config to build alone.")
            parser.add_argument("--out_dir", "-o", type=str,
                            help="Output to this folder (overrides config file)")
            parser.add_argument("--pages", type=str, help="Markdown file(s) to build "+\
                                "that aren't described in the config.", nargs="+")
            parser.add_argument("--no_cover", "-n", action="store_true",
                                help="Don't automatically add a cover / index file.")
            parser.add_argument("--skip_preprocessor", action="store_true", default=False,
                                help="Don't pre-process Jinja syntax in markdown files")
            parser.add_argument("--title", type=str, help="Override target display "+\
                                "name. Useful when passing multiple args to --pages.")
            parser.add_argument("--vars", type=str, help="A YAML or JSON file with vars "+
                                "to add to the target so the preprocessor and "+
                                "templates can reference them.")
            parser.add_argument("--watch", "-w", action="store_true",
                                help="Watch for changes and re-generate output. "+\
                                "This runs until force-quit.")

        elif utility == self.UTIL_LINKS:
            parser.add_argument("-o", "--offline", action="store_true",
               help="Check local anchors only")
            parser.add_argument("-s", "--strict", action="store_true",
                help="Exit with error even on known problems")
            parser.add_argument("-n", "--no_final_retry", action="store_true",
                help="Don't wait and retry failed remote links at the end.")

        self.cli_args = parser.parse_args()
