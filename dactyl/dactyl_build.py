#!/usr/bin/env python3

################################################################################
# Dactyl - a tool for heroic epics of documentation
#
# Generates a website from Markdown and Jinja templates, with filtering
# along the way.
################################################################################

from dactyl.common import *

# Necessary to copy static files to the output dir
from distutils.dir_util import copy_tree, remove_tree
from shutil import copy as copy_file

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
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from dactyl.config import DactylConfig
from dactyl.cli import DactylCLIParser

# These fields are special, and pages don't inherit them directly
RESERVED_KEYS_TARGET = [
    "name",
    "display_name",
    "pages",
]
ADHOC_TARGET = "__ADHOC__"
ES_EVAL_KEY = "__dactyl_eval__"

def target_slug_name(target):
    """Make a name for the target that's safe for use in URLs, filenames, and
    similar places (ElasticSearch index names too) from human-readable fields"""
    target = get_target(target)
    filename_segments = []
    for fieldname in config["pdf_filename_fields"]:
        if fieldname in target.keys():
            filename_segments.append(slugify(target[fieldname]))

    if filename_segments:
        return config["pdf_filename_separator"].join(filename_segments)
    else:
        return slugify(target["name"])

def default_pdf_name(target):
    """Choose a reasonable name for a PDF file in case one isn't specified."""
    return target_slug_name(target)+".pdf"


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

def get_filters_for_page(page, target=None):
    ffp = set(config["default_filters"])
    target = get_target(target)
    if "filters" in target:
        ffp.update(target["filters"])
    if "filters" in page:
        ffp.update(page["filters"])
    loaded_filters = set(config.filters.keys())
    # logger.debug("Removing unloaded filters from page %s...\n  Before: %s"%(page,ffp))
    ffp &= loaded_filters
    # logger.debug("  After: %s"%ffp)
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
    try:
        md = preprocess_markdown(page,
            target=target,
            categories=categories,
            mode=mode,
            current_time=current_time,
            page_filters=page_filters,
            bypass_errors=bypass_errors,
        )
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        recoverable_error("Couldn't preprocess markdown for page %s: %s" %
                (page["name"], repr(e)), bypass_errors)
        # Just fetch the md without running the preprocessor
        md = preprocess_markdown(page,
            target=target,
            categories=categories,
            mode=mode,
            current_time=current_time,
            page_filters=page_filters,
            bypass_errors=bypass_errors,
            skip_preprocessor=True
        )

    # Actually parse the markdown
    logger.info("... parsing markdown...")
    html = markdown(md, extensions=["markdown.extensions.extra",
                                    "markdown.extensions.toc"],
                    lazy_ol=False)

    # Apply raw-HTML-string-based filters here
    for filter_name in page_filters:
        if "filter_html" in dir(config.filters[filter_name]):
            logger.info("... applying HTML filter %s" % filter_name)
            html = config.filters[filter_name].filter_html(
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
        if "filter_soup" in dir(config.filters[filter_name]):
            logger.info("... applying soup filter %s" % filter_name)
            config.filters[filter_name].filter_soup(
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
                        bypass_errors=False, skip_preprocessor="NOT SPECIFIED"):
    """Read a markdown file, local or remote, and preprocess it, returning the
    preprocessed text."""
    target=get_target(target)
    pages=get_pages(target, bypass_errors)

    if skip_preprocessor=="NOT SPECIFIED":
        skip_preprocessor = config["skip_preprocessor"]

    if skip_preprocessor:
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
        if "filter_markdown" in dir(config.filters[filter_name]):
            logger.info("... applying markdown filter %s" % filter_name)
            md = config.filters[filter_name].filter_markdown(
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


def setup_pp_env(page=None, page_filters=[], no_loader=False):
    remote, path = get_page_where(page)
    if remote:
        logger.debug("Using remote template loader for page %s" % page)
        pp_env = jinja2.Environment(loader=jinja2.FunctionLoader(read_markdown_remote))
    elif no_loader:
        logger.debug("Using a no-loader Jinja environment")
        pp_env = jinja2.Environment()
    else:
        logger.debug("Using FileSystemLoader for page %s" % page)
        pp_env = jinja2.Environment(loader=jinja2.FileSystemLoader(path))

    # Pull exported values (& functions) from page filters into the pp_env
    for filter_name in page_filters:
        if filter_name not in config.filters.keys():
            logger.debug("Skipping unloaded filter '%s'" % filter_name)
            continue
        if "export" in dir(config.filters[filter_name]):
            for key,val in config.filters[filter_name].export.items():
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
                 (currentpage["name"], repr(e)), bypass_errors)
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

def add_bonus_fields(currentpage, target=None, pages=None, categories=[],
        mode="html", current_time="", bypass_errors=False):
    """Adds several metadata fields to a page based on the process of rendering
    it into HTML, including plaintext, blurb, and headermap"""
    body_html = parse_markdown(
        currentpage,
        target=target,
        pages=pages,
        mode=mode,
        current_time=current_time,
        categories=categories,
        bypass_errors=bypass_errors,
    )
    soup = BeautifulSoup(body_html, "html.parser")

    # Get "true" plaintext of the page
    currentpage["plaintext"] = soup.get_text()

    # Get a map of all headers
    headermap = {}
    headers = soup.find_all(re.compile("h[1-6]"), id=True)
    currentpage["headermap"] = {h.get_text(): "#" + h["id"] for h in headers}

    # Make a blurb from the first non-empty paragraph if no blurb is defined
    if "blurb" not in currentpage:
        p = soup.find("p")
        while p:
            if p.get_text().strip():
                currentpage["blurb"] = p.get_text()
                break
            else:
                p = p.find_next_sibling("p")
        else:
            logger.debug("Couldn't find a paragraph with text in %s." % currentpage)
            # Fall back to reusing the page name as the blurb
            currentpage["blurb"] = currentpage["name"]


def eval_es_string(expr, context):
    try:
        result = eval(expr, {}, context)
    except Exception as e:
        recoverable_error("__dactyl_eval__ failed on expression '%s': %s" %
            (expr, repr(e)), context["bypass_errors"])
        result = expr
    return result

def render_es_json(currentpage, es_template, pages=[], target=None, categories=[],
                    page_filters=[], mode="es", current_time="TIME_UNKNOWN",
                    bypass_errors=False):
    """Returns stringified JSON representing the currentpage"""

    # This method modifies the currentpage dictionary inline:
    add_bonus_fields(
        currentpage,
        target=target,
        mode=mode,
        current_time=current_time,
        categories=categories,
        bypass_errors=bypass_errors,
    )

    context = {
        "currentpage": currentpage,
        "target": target,
        "categories": categories,
        "page_filters": page_filters,
        "mode": mode,
        "current_time": current_time,
        "bypass_errors": bypass_errors,
    }

    es_env = setup_pp_env(no_loader=True)

    def render_es_field(value, context):
        if type(value) == str: # jinja-render strings
            field_templ = es_env.from_string(value)
            try:
                parsed_field = field_templ.render(context)
            except jinja2.exceptions.TemplateSyntaxError as e:
                recoverable_error("Couldn't parse value '%s' in ES template: %s" %
                    (value, e), bypass_errors)
            return parsed_field
        elif type(value) in (type(None), int, float, bool): # preserve literals
            return value
        elif type(value) == dict and ES_EVAL_KEY in value.keys():
            return eval_es_string(value[ES_EVAL_KEY], context)
        elif type(value) == dict: # recurse!
            return {rkey: render_es_field(rval, context) for rkey,rval in value.items()}
        elif type(value) == list: # recurse!
            return [render_es_field(rval, context) for rval in value]
        else:
            recoverable_error("Unknown type in ES template: %s"%type(value))

    wout = {key: render_es_field(val, context) for key,val in es_template.items()}
    return json.dumps(wout, indent=4, separators=(',', ': '))

def get_es_instance(es_base_url):
    if es_base_url == DEFAULT_ES_URL:
        # Pull it from the config file
        es_base_url = config.get("elasticsearch", "http://localhost:9200")

        # Make sure it has an http:// or https:// prefix
    if es_base_url[:7] != "http://" and es_base_url[:8] != "https://":
        es_base_url = "https://"+es_base_url

    if es_base_url[-1] == "/": # Drop trailing slash
        es_base_url = es_base_url[:-1]

    logger.debug("ElasticSearch base URL is '%s'" % es_base_url)
    return es_base_url

def upload_es_json(es_json, es_index, es_base, id, doc_type='article'):
    """Uploads a document to the ElasticSearch index."""

    # Using requests
    url = "{es_base}/{index}/{doc_type}/{id}".format(
        es_base=es_base,
        index=es_index.lower(), # ES index names must be lowercase
        doc_type=doc_type,
        id=id,
    )
    headers = {"Content-Type": "application/json"}
    logger.info("Uploading to ES: PUT %s" % url)
    r = requests.put(url, headers=headers, data=es_json)
    if r.status_code >= 400:
        recoverable_error("ES upload failed with error: '%s'" % r.text,
                config.bypass_errors)


def render_pages(target=None, mode="html", bypass_errors=False,
                only_page=False, temp_files_path=None, es_upload=NO_ES_UP):
    """Parse and render all pages in target, writing files to out_path."""
    target = get_target(target)
    pages = get_pages(target, bypass_errors)
    categories = get_categories(pages)
    current_time = time.strftime(config["time_format"]) # Get time once only

    if es_upload != NO_ES_UP:
        es_base_url = get_es_instance(es_upload)
        es_index = target_slug_name(target)
        # Note: this doesn't delete the old index

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
    elif mode == "es":
        out_path = config["out_path"]
    else:
        exit("Unknown mode %s" % mode)
    if mode == "es" or es_upload != NO_ES_UP:
        default_es_template = config.get_es_template(config["default_es_template"])

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
        elif mode == "es":
            filepath = re.sub(r'(.+)\.html?$', r'\1.json', currentpage["html"], flags=re.I)

        if mode == "es" or es_upload != NO_ES_UP:
            if "es_template" in currentpage:
                es_template = config.get_es_template(currentpage["es_template"])
            else:
                es_template = default_es_template

        if "md" in currentpage and (mode == "es" or es_upload != NO_ES_UP):
            # Generate the ES JSON & upload it first; save it for es mode
            # so we don't end up having to build the JSON twice in es mode
            try:
                es_json_s = render_es_json(currentpage,
                    es_template,
                    target=target,
                    pages=pages,
                    categories=categories,
                    mode=mode,
                    current_time=current_time,
                    page_filters=get_filters_for_page(currentpage, target),
                    bypass_errors=bypass_errors,)
                if es_upload != NO_ES_UP:
                    es_page_id = target["name"]+"."+currentpage["html"]
                    upload_es_json(es_json_s, es_index, es_base_url, es_page_id)
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                recoverable_error( ("Skipping ES build/upload of %s " +
                          "due to error: %s") %
                           (currentpage["name"], repr(e)), bypass_errors)
                es_json_s = "{}"

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
                recoverable_error( ("Preprocessing page %s failed " +
                          "with error: %s") %
                           (currentpage["name"], repr(e)), bypass_errors)
        elif mode == "es":
            if "md" not in currentpage:
                logger.info("es mode: Skipping page (no md content): %s" % currentpage)
                continue
            page_text = es_json_s

        else:
            exit("render_pages error: unknown mode: %s" % mode)

        # Finally, write the rendered page
        write_page(page_text, filepath, out_path)

    if only_page and not matched_only:
        exit("Didn't find requested 'only' page '%s'" % only_page)

# def make_esj(target=target, bypass_errors=cli_args.bypass_errors,
#             only_page=cli_args.only,):
#     """Build .json files to be uploaded to ElasticSearch for pages in target."""
#

def write_page(page_text, filepath, out_path):
    out_folder = os.path.join(out_path, os.path.dirname(filepath))
    if not os.path.isdir(out_folder):
        logger.info("creating output folder %s" % out_folder)
        os.makedirs(out_folder)
    fileout = os.path.join(out_path, filepath)
    with open(fileout, "w") as f:
        logger.info("writing to file: %s..." % fileout)
        f.write(page_text)


def watch(mode, target, only_page="", pdf_file=DEFAULT_PDF_FILE,
          es_upload=NO_ES_UP):
    """Look for changed files and re-run the build whenever there's an update.
       Runs until interrupted."""
    target = get_target(target)

    class UpdaterHandler(PatternMatchingEventHandler):
        """Updates to pattern-matched files means rendering."""
        def on_any_event(self, event):
            logger.info("got event!")
            # bypass_errors=True because Watch shouldn't
            #  just die if a file is temporarily not found
            if mode == "pdf":
                make_pdf(pdf_file, target=target, bypass_errors=True,
                    only_page=only_page, es_upload=es_upload)
            else:
                render_pages(target, mode=mode, bypass_errors=True,
                            only_page=only_page, es_upload=es_upload)
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


def make_pdf(outfile, target=None, bypass_errors=False, remove_tmp=True,
        only_page="", es_upload=NO_ES_UP):
    """Use prince to convert several HTML files into a PDF"""
    logger.info("rendering PDF-able versions of pages...")
    target = get_target(target)

    temp_files_path = temp_dir()
    render_pages(target=target, mode="pdf", bypass_errors=bypass_errors,
            temp_files_path=temp_files_path, only_page=only_page,
            es_upload=es_upload)

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

def list_targets():
    rows = []
    for t in config["targets"]:
        if "display_name" in t:
            display_name = t["display_name"]
        else:
            filename_field_vals = [t[f] for
                    f in config["pdf_filename_fields"]
                    if f in t.keys()]
            display_name = " ".join(filename_field_vals)
        rows.append((t["name"], display_name))

    col1_width = max([len(i) for i,j in rows]) + 3
    for row in rows:
        print("{row[0]:{width}} {row[1]}".format(row=row, width=col1_width))

def main(cli_args):
    if cli_args.list_targets_only:
        list_targets()
        exit(0)

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
            exit("FATAL: --vars value was improperly formatted: %s" % repr(e))

    if cli_args.title:
        target["display_name"] = cli_args.title

    if not cli_args.no_cover and not target.get("no_cover", False):
        # Add the default cover as the first page of the target
        coverpage = config["cover_page"]
        coverpage["targets"] = [target["name"]]
        config["pages"].insert(0, coverpage)

    if cli_args.pdf != NO_PDF:
        mode = "pdf"
        logger.info("making a pdf...")
        make_pdf(cli_args.pdf,
                target=target,
                bypass_errors=cli_args.bypass_errors,
                remove_tmp=(not cli_args.leave_temp_files),
                only_page=cli_args.only,
                es_upload=cli_args.es_upload,
        )
        logger.info("pdf done")
    else:
        # Set mode and default content/template static copy settings
        if cli_args.md:
            mode = "md"
            content_static = True
            template_static = False
        elif cli_args.es:
            mode = "es"
            content_static = False
            template_static = False
        else:
            mode = "html"
            content_static = True
            template_static = True

        # Override static files copy setting based on CLI flags, if any are used
        if cli_args.no_static:
            content_static = False
            template_static = False
        elif cli_args.template_static:
            content_static = False
            template_static = True
        elif cli_args.content_static:
            content_static = True
            template_static = False
        elif cli_args.copy_static:
            content_static = True
            template_static = True


        logger.info("rendering %s..." % mode)
        render_pages(target=target,
                     bypass_errors=cli_args.bypass_errors,
                     only_page=cli_args.only,
                     mode=mode,
                     es_upload=cli_args.es_upload,
        )
        logger.info("done rendering %s" % mode)
        if content_static or template_static:
            logger.info("outputting static files...")
            copy_static_files(template_static=template_static,
                              content_static=content_static)

    if cli_args.watch:
        logger.info("watching for changes...")
        watch(mode, target, cli_args.only, cli_args.pdf,
                es_upload=cli_args.es_upload,)


def dispatch_main():
    cli = DactylCLIParser(DactylCLIParser.UTIL_BUILD)
    global config
    config = DactylConfig(cli.cli_args)
    config.load_build_options()
    main(cli.cli_args)


if __name__ == "__main__":
    dispatch_main()
