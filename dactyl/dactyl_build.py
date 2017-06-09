#!/usr/bin/env python3

################################################################################
# Dactyl - a tool for heroic epics of documentation
#
# Generates a website from Markdown and Jinja templates, with filtering
# along the way.
################################################################################

DEFAULT_CONFIG_FILE = "dactyl-config.yml"

import os
import re
import yaml
import argparse
import logging
import traceback

# Necessary to copy static files to the output dir
from distutils.dir_util import copy_tree, remove_tree
from shutil import copy as copy_file

# Used for pulling in the default config file
from pkg_resources import resource_stream

# Used to import filters.
from importlib import import_module
import importlib.util

# Necessary for prince
import subprocess

# Used to fetch markdown sources from the net
import requests
from urllib.parse import urlparse

# Various content and template processing stuff
import jinja2
from markdown import markdown
from bs4 import BeautifulSoup

# Watchdog stuff
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from dactyl.version import __version__

# The log level is configurable at runtime (see __main__ below)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

# These fields are special, and pages don't inherit them directly
RESERVED_KEYS_TARGET = [
    "name",
    "display_name",
    # "filters",
    "pages",
]
ADHOC_TARGET = "__ADHOC__"
DEFAULT_PDF_FILE = "__DEFAULT_FILENAME__"
NO_PDF = "__NO_PDF__"

config = yaml.load(resource_stream(__name__, "default-config.yml"))


filters = {}
def load_config(config_file=DEFAULT_CONFIG_FILE, bypass_errors=False):
    """Reload config from a YAML file."""
    global config, filters
    logger.debug("loading config file %s..." % config_file)
    try:
        with open(config_file, "r") as f:
            loaded_config = yaml.load(f)
    except FileNotFoundError as e:
        if config_file == DEFAULT_CONFIG_FILE:
            logger.info("Couldn't read a config file; using generic config")
            loaded_config = {}
        else:
            traceback.print_tb(e.__traceback__)
            exit("Fatal: Config file '%s' not found"%config_file)
    except yaml.parser.ParserError as e:
        traceback.print_tb(e.__traceback__)
        exit("Fatal: Error parsing config file: %s"%e)

    # Migrate legacy config fields
    if "pdf_template" in loaded_config:
        if "default_pdf_template" in loaded_config:
            recoverable_error("Ignoring redundant global config option "+
                           "pdf_template in favor of default_pdf_template",
                           bypass_errors)
        else:
            loaded_config["default_pdf_template"] = loaded_config["pdf_template"]
            logger.warning("Deprecation warning: Global field pdf_template has "
                          +"been renamed default_pdf_template")

    config.update(loaded_config)

    targetnames = set()
    for t in config["targets"]:
        if "name" not in t:
            logger.error("Target does not have required 'name' field: %s" % t)
            exit(1)
        elif t["name"] in targetnames:
            recoverable_error("Duplicate target name in config file: '%s'" %
                t["name"], bypass_errors)
        targetnames.add(t["name"])
    
    # Check page list for consistency and provide default values
    for page in config["pages"]:
        if "targets" not in page:
            if "name" in page:
                logger.warning("Page %s is not part of any targets." %
                             page["name"])
            else:
                logger.warning("Page %s is not part of any targets." % page)
        elif type(page["targets"]) != list:
            recoverable_error(("targets parameter specified incorrectly; "+
                              "must be a list. Page: %s") % page, bypass_errors)
        elif set(page["targets"]).difference(targetnames):
            recoverable_error("Page '%s' contains undefined targets: %s" %
                        (page, set(page["targets"]).difference(targetnames)),
                        bypass_errors)
        if "md" in page and "name" not in page:
            logger.debug("Guessing page name for page %s" % page)
            page_path = os.path.join(config["content_path"], page["md"])
            page["name"] = guess_title_from_md_file(page_path)

        if "html" not in page:
            page["html"] = html_filename_from(page)



    # Figure out which filters we need
    filternames = set(config["default_filters"])
    for target in config["targets"]:
        if "filters" in target:
            filternames.update(target["filters"])
    for page in config["pages"]:
        if "filters" in page:
            filternames.update(page["filters"])

    load_filters(filternames)

def load_filters(filternames):
    global filters
    for filter_name in filternames:
        filter_loaded = False
        if "filter_paths" in config:
            for filter_path in config["filter_paths"]:
                try:
                    f_filepath = os.path.join(filter_path, "filter_"+filter_name+".py")
                    spec = importlib.util.spec_from_file_location(
                                "dactyl_filters."+filter_name, f_filepath)
                    filters[filter_name] = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(filters[filter_name])
                    filter_loaded = True
                    break
                except Exception as e:
                    logger.debug("Filter %s isn't in path %s\nErr:%s" %
                                (filter_name, filter_path, e))

        if not filter_loaded:
            # Load from the Dactyl module
            filters[filter_name] = import_module("dactyl.filter_"+filter_name)

def default_pdf_name(target):
    target = get_target(target)
    filename_segments = []
    for fieldname in config["pdf_filename_fields"]:
        if fieldname in target.keys():
            filename_segments.append(slugify(target[fieldname]))

    if filename_segments:
        return config["pdf_filename_separator"].join(filename_segments) + ".pdf"
    else:
        return slugify(target["name"])+".pdf"


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

# Generate a unique nonce per-run to be used for tempdir folder names
nonce = str(time.time()).replace(".","")
def temp_dir():
    run_dir = os.path.join(config["temporary_files_path"],
                      "dactyl-"+nonce)
    if not os.path.isdir(run_dir):
        os.makedirs(run_dir)
    return run_dir

def get_target(target):
    """Get a target by name, or return the default target object.
       We can't use default args in function defs because the default is
       set at runtime based on config"""
    if target == None:
        logger.debug("get_target: using target #0")
        if len(config["targets"]) == 0:
            exit("No targets found. Either specify a config file or --pages")
        return config["targets"][0]

    if type(target) == str:
        try:
            return next(t for t in config["targets"] if t["name"] == target)
        except StopIteration:
            logger.critical("Unknown target: %s" % target)
            exit(1)

    if "name" in target:
        # Eh, it's probably a target, just return it
        return target


def make_adhoc_target(inpages):
    t = {
        "name": ADHOC_TARGET,
        "display_name": "(Untitled)",
    }

    if len(inpages) == 1:
        t["display_name"] = guess_title_from_md_file(inpages[0])

    for inpage in inpages:
        # Figure out the actual filename and location of this infile
        # and set the content source dir appropriately
        in_dir, in_file = os.path.split(inpage)
        config["content_path"] = in_dir

        # Figure out what html file to output to
        ENDS_IN_MD = re.compile("\.md$", re.I)
        if re.search(ENDS_IN_MD, in_file):
            out_html_file = re.sub(ENDS_IN_MD, ".html", in_file)
        else:
            out_html_file = in_file+".html"

        # Try to come up with a reasonable page title
        page_title = guess_title_from_md_file(inpage)

        new_page = {
            "name": page_title,
            "md": in_file,
            "html": out_html_file,
            "targets": [ADHOC_TARGET],
            "category": "Pages",
            "pp_dir": in_dir,
        }
        config["pages"].append(new_page)

    config["targets"].append(t)

    return t


def guess_title_from_md_file(filepath):
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


def get_filters_for_page(page, target=None):
    ffp = set(config["default_filters"])
    target = get_target(target)
    if "filters" in target:
        ffp.update(target["filters"])
    if "filters" in page:
        ffp.update(page["filters"])
    return ffp


def parse_markdown(page, target=None, pages=None, categories=[], mode="html",
                    current_time="", bypass_errors=False):
    """Takes a page object (must contain "md" attribute) and returns parsed
    and filtered HTML."""
    target = get_target(target)

    logger.info("Preparing page %s" % page["name"])

    # We'll apply these filters to the page
    page_filters = get_filters_for_page(page, target)

    # Get the markdown, preprocess, and apply md filters
    md = preprocess_markdown(page,
        target=target,
        categories=categories,
        mode=mode,
        current_time=current_time,
        page_filters=page_filters,
        bypass_errors=bypass_errors,
    )

    # Actually parse the markdown
    logger.info("... parsing markdown...")
    html = markdown(md, extensions=["markdown.extensions.extra",
                                    "markdown.extensions.toc"],
                    lazy_ol=False)

    # Apply raw-HTML-string-based filters here
    for filter_name in page_filters:
        if "filter_html" in dir(filters[filter_name]):
            logger.info("... applying HTML filter %s" % filter_name)
            html = filters[filter_name].filter_html(
                    html,
                    currentpage=page,
                    categories=categories,
                    pages=pages,
                    target=target,
                    current_time=current_time,
                    mode=mode,
                    config=config,
                    logger=logger,
            )

    # Some filters would rather operate on a soup than a string.
    # May as well parse once and re-serialize once.
    soup = BeautifulSoup(html, "html.parser")

    # Apply soup-based filters here
    for filter_name in page_filters:
        if "filter_soup" in dir(filters[filter_name]):
            logger.info("... applying soup filter %s" % filter_name)
            filters[filter_name].filter_soup(
                    soup,
                    currentpage=page,
                    categories=categories,
                    pages=pages,
                    target=target,
                    current_time=current_time,
                    mode=mode,
                    config=config,
                    logger=logger,
            )
            # ^ the soup filters apply to the same object, passed by reference

    logger.info("... re-rendering HTML from soup...")
    html2 = str(soup)
    return html2


def html_filename_from(page):
    """Take a page definition and choose a reasonable HTML filename for it."""
    if "md" in page:
        new_filename = re.sub(r"[.]md$", ".html", page["md"])
        if config.get("flatten_default_html_paths", True):
            return new_filename.replace(os.sep, "-")
        else:
            return new_filename
    elif "name" in page:
        return slugify(page["name"]).lower()+".html"
    else:
        new_filename = str(time.time()).replace(".", "-")+".html"
        logger.debug("Generated filename '%s' for page: %s" %
                    (new_filename, page))
        return new_filename


def get_pages(target=None, bypass_errors=False):
    """Read pages from config and return an object, optionally filtered
       to just the pages that this target cares about"""

    target = get_target(target)
    pages = config["pages"]

    if target["name"]:
        #filter pages that aren't part of this target
        pages = [page for page in pages
                 if should_include(page, target["name"])]

    # Check for pages that would overwrite each other
    html_outs_in_target = []
    for p in pages:
        if p["html"] in html_outs_in_target:
            recoverable_error(("Repeated output filename '%s': "+
                "the earlier instances will be overwritten") % p["html"],
                bypass_errors)
        html_outs_in_target.append(p["html"])

    # Pages should inherit non-reserved keys from the target
    for p in pages:
        merge_dicts(target, p, RESERVED_KEYS_TARGET)

    return pages

def should_include(page, target_name):
    """Report whether a given page should be part of the given target"""
    if "targets" not in page:
        return False
    if target_name in page["targets"]:
        return True
    else:
        return False

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

def get_categories(pages):
    """Produce an ordered, de-duplicated list of categories from
       the page list"""
    categories = []
    for page in pages:
        if "category" in page and page["category"] not in categories:
            categories.append(page["category"])
    logger.debug("categories: %s" % categories)
    return categories

def preprocess_markdown(page, target=None, categories=[], page_filters=[],
                        mode="html", current_time="TIME_UNKNOWN",
                        bypass_errors=False):
    """Read a markdown file, local or remote, and preprocess it, returning the
    preprocessed text."""
    target=get_target(target)
    pages=get_pages(target, bypass_errors)

    if config["skip_preprocessor"]:
        remote, basepath = get_page_where(page)
        if remote:
            logger.info("... reading markdown from URL.")
            md = read_markdown_remote(page["md"])
        else:
            logger.info("... reading markdown from file")
            with open(page["md"], "r") as f:
                md = f.read()

    else:
        pp_env = setup_pp_env(page, page_filters=page_filters)
        md_raw = pp_env.get_template(page["md"])
        md = md_raw.render(
            currentpage=page,
            categories=categories,
            pages=pages,
            target=target,
            current_time=current_time,
            mode=mode,
            config=config
        )


    # Apply markdown-based filters here
    for filter_name in page_filters:
        if "filter_markdown" in dir(filters[filter_name]):
            logger.info("... applying markdown filter %s" % filter_name)
            md = filters[filter_name].filter_markdown(
                md,
                currentpage=page,
                categories=categories,
                pages=pages,
                target=target,
                current_time=current_time,
                mode=mode,
                config=config,
                logger=logger,
            )

    logger.info("... markdown is ready")
    return md


def read_markdown_remote(url):
    """Fetch a remote markdown file and return its contents"""
    parsed_url = urlparse(url)

    # save this base URL if it's new; that way we can try to let remote
    # templates inherit from other templates at related URLs
    if parsed_url.scheme or "baseurl" not in dir(read_markdown_remote):
        base_path = os.path.dirname(parsed_url.path)
        read_markdown_remote.baseurl = (
            parsed_url[0],
            parsed_url[1],
            base_path,
            parsed_url[3],
            parsed_url[4],
            parsed_url[5],
        )
    # if we're at read_markdown_remote without a scheme, it's probably a remote
    # template trying to import another template, so let's assume it's from the
    # base path of the imported template
    if not parsed_url.scheme:
        url = os.path.join(read_markdown_remote.baseurl, url)

    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise requests.RequestException("Status code for page was not 200")


def copy_static_files(template_static=True, content_static=True, out_path=None):
    """Copy static files to the output directory."""
    if out_path == None:
        out_path = config["out_path"]

    if template_static:
        template_static_src = config["template_static_path"]

        if os.path.isdir(template_static_src):
            template_static_dst = os.path.join(out_path,
                                       os.path.basename(template_static_src))
            copy_tree(template_static_src, template_static_dst)
        else:
            logger.warning(("Template` static path '%s' doesn't exist; "+
                            "skipping.") % template_static_src)

    if content_static:
        if "content_static_path" in config:
            if type(config["content_static_path"]) == str:
                content_static_srcs = [config["content_static_path"]]
            else:
                content_static_srcs = config["content_static_path"]

            for content_static_src in content_static_srcs:
                if os.path.isdir(content_static_src):
                    content_static_dst = os.path.join(out_path,
                                        os.path.basename(content_static_src))
                    copy_tree(content_static_src, content_static_dst)
                elif os.path.isfile(content_static_src):
                    content_static_dst = os.path.join(out_path,
                                        os.path.dirname(content_static_src))
                    logger.debug("Copying single content_static_path file '%s'." %
                            content_static_src)
                    copy_file(content_static_src, content_static_dst)
                else:
                    logger.warning("Content static path '%s' doesn't exist; skipping." %
                                    content_static_src)
        else:
            logger.debug("No content_static_path in conf; skipping copy")


def get_page_where(page=None):
    """Returns a (remote, path) tuple where remote is a boolean and path is the
    URL or file path."""
    if not page:
        return False, config["content_path"]
    elif "pp_dir" in page:
        return False, page["pp_dir"]
    elif "md" in page and (page["md"][:5] == "http:" or
                page["md"][:6] == "https:"):
        return True, os.path.dirname(page["md"])
    else:
        return False, config["content_path"]


def setup_pp_env(page=None, page_filters=[]):
    remote, path = get_page_where(page)
    if remote:
        logger.debug("Using remote template loader for page %s" % page)
        pp_env = jinja2.Environment(loader=jinja2.FunctionLoader(read_markdown_remote))
    else:
        logger.debug("Using FileSystemLoader for page %s" % page)
        pp_env = jinja2.Environment(loader=jinja2.FileSystemLoader(path))

    # Pull exported values (& functions) from page filters into the pp_env
    for filter_name in page_filters:
        if "export" in dir(filters[filter_name]):
            for key,val in filters[filter_name].export.items():
                logger.debug("... pulling in filter_%s's exported key '%s'" % (filter_name, key))
                pp_env.globals[key] = val
    return pp_env


def setup_html_env():
    if "template_path" in config:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(config["template_path"]))
    else:
        env = setup_fallback_env()
    env.lstrip_blocks = True
    env.trim_blocks = True
    return env


def setup_fallback_env():
    env = jinja2.Environment(loader=jinja2.PackageLoader(__name__))
    env.lstrip_blocks = True
    env.trim_blocks = True
    return env

def toc_from_headers(html_string):
    """make a table of contents from headers"""
    soup = BeautifulSoup(html_string, "html.parser")
    headers = soup.find_all(name=re.compile("h[1-3]"), id=True)
    toc_s = ""
    for h in headers:
        if h.name == "h1":
            toc_level = "level-1"
        elif h.name == "h2":
            toc_level = "level-2"
        else:
            toc_level = "level-3"

        new_a = soup.new_tag("a", href="#"+h["id"])
        if h.string:
            new_a.string = h.string
        else:
            new_a.string = " ".join(h.strings)
        new_li = soup.new_tag("li")
        new_li["class"] = toc_level
        new_li.append(new_a)

        toc_s += str(new_li)+"\n"

    return str(toc_s)


def safe_get_template(template_name, env, fallback_env):
    """
    Gets the named Jinja template from the specified template path if it exists,
    and falls back to the Dactyl built-in templates if it doesn't.
    """
    try:
        t = env.get_template(template_name)
    except jinja2.exceptions.TemplateNotFound:
        logger.warning("falling back to Dactyl built-ins for template %s" % template_name)
        t = fallback_env.get_template(template_name)
    return t

def match_only_page(only_page, currentpage):
    """Returns a boolean indicating whether currentpage (object) matches the
    only_page parameter (string)"""
    if not only_page:
        return False
    if only_page[-5:] == ".html":
        if (currentpage["html"] == only_page or
                os.path.basename(currentpage["html"]) == only_page):
            return True
    elif only_page[-3:] == ".md":
        if "md" in currentpage and (currentpage["md"] == only_page or
                os.path.basename(currentpage["md"]) == only_page):
            return True
    return False

def render_page(currentpage, target, pages, mode, current_time, categories,
        use_template, bypass_errors=False):
    if "md" in currentpage:
        # Read and parse the markdown
        try:
            html_content = parse_markdown(
                currentpage,
                target=target,
                pages=pages,
                mode=mode,
                current_time=current_time,
                categories=categories,
                bypass_errors=bypass_errors,
            )

        except Exception as e:
            traceback.print_tb(e.__traceback__)
            recoverable_error("Error when fetching page %s: %s" %
                 (currentpage["name"], e), bypass_errors)
            html_content=""

    else:
        html_content = ""

    # Prepare some parameters for rendering
    page_toc = toc_from_headers(html_content)

    # Render the content into the appropriate template
    out_html = use_template.render(
        currentpage=currentpage,
        categories=categories,
        pages=pages,
        content=html_content,
        target=target,
        current_time=current_time,
        sidebar_content=page_toc, # legacy
        page_toc=page_toc,
        mode=mode,
        config=config
    )
    return out_html

def render_pages(target=None, mode="html", bypass_errors=False,
                only_page=False, temp_files_path=None):
    """Parse and render all pages in target, writing files to out_path."""
    target = get_target(target)
    pages = get_pages(target, bypass_errors)
    categories = get_categories(pages)
    current_time = time.strftime(config["time_format"]) # Get time once only

    if mode == "pdf" or mode == "html":
        # Insert generated HTML into templates using this Jinja environment
        env = setup_html_env()
        fallback_env = setup_fallback_env()
    if mode == "pdf":
        out_path = temp_files_path or temp_dir()
        default_template = safe_get_template(config["default_pdf_template"], env, fallback_env)
    elif mode == "html":
        out_path = config["out_path"]
        default_template = safe_get_template(config["default_template"], env, fallback_env)
    elif mode == "md":
        out_path = config["out_path"]
    else:
        exit("Unknown mode %s" % mode)

    matched_only = False
    for currentpage in pages:
        if only_page:
            if match_only_page(only_page, currentpage):
                matched_only = True
            else:
                logger.debug("only_page mode: skipping page %s" % currentpage)
                continue

        if mode == "html":
            filepath = currentpage["html"]
            if "template" in currentpage:
                use_template = safe_get_template(currentpage["template"], env, fallback_env)
            else:
                use_template = default_template
        elif mode == "pdf":
            filepath = currentpage["html"] # Used in the temp dir
            if "pdf_template" in currentpage:
                use_template = safe_get_template(currentpage["pdf_template"], env, fallback_env)
            else:
                use_template = default_template

        if mode == "html" or mode == "pdf":
            logger.debug("use_template is: %s" % use_template)
            page_text = render_page(
                currentpage,
                target,
                pages,
                mode,
                current_time,
                categories,
                use_template,
                bypass_errors=bypass_errors
            )
        elif mode == "md":
            if "md" not in currentpage:
                logger.info("md mode: Skipping page (no md): %s" % currentpage)
                continue
            filepath = currentpage["md"]
            try:
                page_text = preprocess_markdown(currentpage,
                    target=target,
                    categories=categories,
                    mode=mode,
                    current_time=current_time,
                    page_filters=get_filters_for_page(currentpage, target),
                    bypass_errors=bypass_errors,
                )
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                recoverable_error( ("Skipping page %s " +
                          "due to error fetching contents: %s") %
                           (currentpage["name"], e), bypass_errors)
                continue

        else:
            exit("render_pages error: unknown mode: %s" % mode)

        # Finally, write the rendered page
        write_page(page_text, filepath, out_path)

    if only_page and not matched_only:
        exit("Didn't find requested 'only' page '%s'" % only_page)

def write_page(page_text, filepath, out_path):
    out_folder = os.path.join(out_path, os.path.dirname(filepath))
    if not os.path.isdir(out_folder):
        logger.info("creating output folder %s" % out_folder)
        os.makedirs(out_folder)
    fileout = os.path.join(out_path, filepath)
    with open(fileout, "w") as f:
        logger.info("writing to file: %s..." % fileout)
        f.write(page_text)


def watch(mode, target, only_page="", pdf_file=DEFAULT_PDF_FILE):
    """Look for changed files and re-generate HTML (and optionally
       PDF whenever there's an update. Runs until interrupted."""
    target = get_target(target)

    class UpdaterHandler(PatternMatchingEventHandler):
        """Updates to pattern-matched files means rendering."""
        def on_any_event(self, event):
            logger.info("got event!")
            # bypass_errors=True because Watch shouldn't
            #  just die if a file is temporarily not found
            if mode == "pdf":
                make_pdf(pdf_file, target=target, bypass_errors=True, only_page=only_page)
            else:
                render_pages(target, mode=mode, bypass_errors=True, only_page=only_page)
            logger.info("done rendering")

    patterns = ["*template-*.html",
                "*.md",
                "*code_samples/*"]

    event_handler = UpdaterHandler(patterns=patterns)
    observer = Observer()
    observer.schedule(event_handler, config["template_path"], recursive=True)
    observer.schedule(event_handler, config["content_path"], recursive=True)
    observer.start()
    # The above starts an observing thread,
    #   so the main thread can just wait
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def make_pdf(outfile, target=None, bypass_errors=False, remove_tmp=True, only_page=""):
    """Use prince to convert several HTML files into a PDF"""
    logger.info("rendering PDF-able versions of pages...")
    target = get_target(target)

    temp_files_path = temp_dir()
    render_pages(target=target, mode="pdf", bypass_errors=bypass_errors,
            temp_files_path=temp_files_path, only_page=only_page)

    # Choose a reasonable default filename if one wasn't provided yet
    if outfile == DEFAULT_PDF_FILE:
        outfile = default_pdf_name(target)

    # Prince will need the static files, so copy them over
    copy_static_files(out_path=temp_files_path)

    # Make sure the path we're going to write the PDF to exists
    if not os.path.isdir(config["out_path"]):
        logger.info("creating output folder %s" % config["out_path"])
        os.makedirs(config["out_path"])
    abs_pdf_path = os.path.abspath(os.path.join(config["out_path"], outfile))

    # Start preparing the prince command
    args = [config["prince_executable"], '--javascript', '-o', abs_pdf_path]
    # Change dir to the tempfiles path; this may avoid a bug in Prince
    old_cwd = os.getcwd()
    os.chdir(temp_files_path)

    pages = get_pages(target, bypass_errors)
    if only_page:
        pages = [p for p in pages if match_only_page(only_page, p)][:1]
        if not len(pages):
            recoverable_error("Couldn't find 'only' page %s" % only_page,
                bypass_errors)
            return
    # Each HTML output file in the target is another arg to prince
    args += [p["html"] for p in pages]

    logger.info("generating PDF: running %s..." % " ".join(args))
    prince_resp = subprocess.check_output(args, universal_newlines=True)
    print(prince_resp)

    # Clean up the tempdir now that we're done using it
    os.chdir(old_cwd)
    if remove_tmp:
        remove_tree(temp_files_path)


def main(cli_args):
    if cli_args.debug:
        logger.setLevel(logging.DEBUG)
    elif not cli_args.quiet:
        logger.setLevel(logging.INFO)

    if cli_args.config:
        load_config(cli_args.config, bypass_errors=cli_args.bypass_errors)
    else:
        load_config(bypass_errors=cli_args.bypass_errors)

    if cli_args.version:
        print("Dactyl version %s" % __version__)
        exit(0)

    if cli_args.list_targets_only:
        for t in config["targets"]:
            if "display_name" in t:
                display_name = t["display_name"]
            else:
                filename_field_vals = [t[f] for
                        f in config["pdf_filename_fields"]
                        if f in t.keys()]
                display_name = " ".join(filename_field_vals)
            print("%s\t\t%s" % (t["name"], display_name))

        exit(0)

    if cli_args.out_dir:
        config["out_path"] = cli_args.out_dir

    config["skip_preprocessor"] = cli_args.skip_preprocessor

    if cli_args.pages:
        make_adhoc_target(cli_args.pages)
        cli_args.target = ADHOC_TARGET

    target = get_target(cli_args.target)

    if cli_args.vars:
        try:
            if cli_args.vars[-5:] in (".json",".yaml"):
                with open(cli_args.vars, "r") as f:
                    custom_keys = yaml.load(f)
            else:
                custom_keys = yaml.load(cli_args.vars)
            for k,v in custom_keys.items():
                if k not in RESERVED_KEYS_TARGET:
                    logger.debug("setting var '%s'='%s'" %(k,v))
                    target[k] = v
                else:
                    raise KeyError("Vars can't include reserved key '%s'" % k)
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            exit("FATAL: --vars value was improperly formatted: %s" % e)

    if cli_args.title:
        target["display_name"] = cli_args.title

    if not cli_args.no_cover and not target.get("no_cover", False):
        # Add the default cover as the first page of the target
        coverpage = config["cover_page"]
        coverpage["targets"] = [target["name"]]
        config["pages"].insert(0, coverpage)

    if cli_args.md:
        mode = "md"
        logger.info("outputting markdown...")
        render_pages(target=cli_args.target,
                     bypass_errors=cli_args.bypass_errors,
                     only_page=cli_args.only,
                     mode="md"
        )
        logger.info("done outputting md files")
        if cli_args.copy_static:
            logger.info("outputting static files...")
            copy_static_files(template_static=False)

    elif cli_args.pdf != NO_PDF:
        mode = "pdf"
        logger.info("making a pdf...")
        make_pdf(cli_args.pdf,
                target=target,
                bypass_errors=cli_args.bypass_errors,
                remove_tmp=(not cli_args.leave_temp_files),
                only_page=cli_args.only,
        )
        logger.info("pdf done")

    else:
        mode = "html"
        logger.info("rendering pages...")
        render_pages(target=cli_args.target,
                     bypass_errors=cli_args.bypass_errors,
                     only_page=cli_args.only,
                     mode="html")
        logger.info("done rendering")

        if cli_args.copy_static:
            logger.info("copying static pages...")
            copy_static_files()

    if cli_args.watch:
        logger.info("watching for changes...")
        watch(mode, target, cli_args.only, cli_args.pdf)


def dispatch_main():
    parser = argparse.ArgumentParser(
        description='Generate static site from markdown and templates.')

    build_mode = parser.add_mutually_exclusive_group(required=False)
    build_mode.add_argument("--pdf", nargs="?", type=str,
                        const=DEFAULT_PDF_FILE, default=NO_PDF,
                        help="Output a PDF to this file. Requires Prince.")
    build_mode.add_argument("--md", action="store_true",
                        help="Output markdown only")
    # HTML is the default mode

    noisiness = parser.add_mutually_exclusive_group(required=False)
    noisiness.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress status messages")
    noisiness.add_argument("--debug", action="store_true",
                        help="Print debug-level log messages")

    parser.add_argument("--watch", "-w", action="store_true",
                        help="Watch for changes and re-generate output. "+\
                         "This runs until force-quit.")
    parser.add_argument("--target", "-t", type=str,
                        help="Build for the specified target.")
    parser.add_argument("--out_dir", "-o", type=str,
                        help="Output to this folder (overrides config file)")
    parser.add_argument("--bypass_errors", "-b", action="store_true",
                        help="Continue building if some contents not found")
    parser.add_argument("--config", "-c", type=str,
                        help="Specify path to an alternate config file.")
    parser.add_argument("--copy_static", "-s", action="store_true",
                        help="Copy static files to the out dir",
                        default=False)
    parser.add_argument("--only", type=str, help=".md or .html filename of a "+
                        "single page in the config to build alone.")
    parser.add_argument("--pages", type=str, help="Markdown file(s) to build "+\
                        "that aren't described in the config.", nargs="+")
    parser.add_argument("--no_cover", "-n", action="store_true",
                        help="Don't automatically add a cover / index file.")
    parser.add_argument("--skip_preprocessor", action="store_true", default=False,
                        help="Don't pre-process Jinja syntax in markdown files")
    parser.add_argument("--title", type=str, help="Override target display "+\
                        "name. Useful when passing multiple args to --pages.")
    parser.add_argument("--leave_temp_files", action="store_true",
                        help="Leave temp files in place (for debugging or "+
                        "manual PDF generation). Ignored when using --watch",
                        default=False)
    parser.add_argument("--vars", type=str, help="A YAML or JSON file with vars "+
                        "to add to the target so the preprocessor and "+
                        "templates can reference them.")

    # The following options cause Dactyl to ignore basically everything else
    parser.add_argument("--version", "-v", action="store_true",
                        help="Print version information and exit.")
    parser.add_argument("--list_targets_only", "-l", action="store_true",
                        help="Don't build anything, just display list of "+
                        "known targets from the config file.")

    cli_args = parser.parse_args()
    main(cli_args)


if __name__ == "__main__":
    dispatch_main()
