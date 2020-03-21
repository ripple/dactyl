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

# shallow copying of data types
from copy import copy

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
from dactyl.target import DactylTarget
from dactyl.page import DactylPage



HOW_FROM_URL = 1
HOW_FROM_GENERATOR = 2
HOW_FROM_FILE = 3


class DactylBuilder:
    def __init__(self, target, config, mode="html", only_page=None):
        assert isinstance(target, DactylTarget)
        self.target = target
        self.config = config
        self.mode = mode
        # Generate a unique nonce per-run to be used for tempdir folder names
        self.nonce = str(time.time()).replace(".","")

        # Set a bunch of settings that can be overwritten after instantiating
        if mode == "html":
            self.copy_content_static = True
            self.copy_template_static = True
        elif mode == "md":
            self.copy_content_static = True
            self.copy_template_static = False
        else:
            self.copy_content_static = False
            self.copy_template_static = False

        self.out_path = self.config["out_path"]
        if mode == "pdf":
            self.out_path = self.temp_dir()

        self.leave_temp_files = False

        if mode == "es":
            self.es_upload = DEFAULT_ES_URL
        else:
            self.es_upload = False

        if (self.config["template_allow_undefined"] == False and
                not self.config.bypass_errors):
            self.strict_undefined = True
        else:
            self.strict_undefined = False

        self.setup_html_env() # sets self.html_env
        self.setup_fallback_env() # sets self.fallback_env

        self.default_pdf_template = self.get_template(self.config["default_pdf_template"])
        self.default_html_template = self.get_template(self.config["default_template"])
        self.default_es_template = self.get_es_template(self.config["default_es_template"])


    def temp_dir(self):
        run_dir = os.path.join(self.config["temporary_files_path"],
                          "dactyl-"+self.nonce)
        if not os.path.isdir(run_dir):
            os.makedirs(run_dir)
        return run_dir

    def build_one(self, only_page):
        """
        Helper for building just a single page from the target.
        """
        self.build_all(only_page=only_page)

    @staticmethod
    def match_only_page(only_page, currentpage):
        """
        Returns a boolean indicating whether currentpage (object) matches the
        only_page parameter (string). Used for build_one()
        """
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

    def build_all(self, only_page=None):
        """
        Build and write all pages in the target, according to the set mode,
        and upload their entries to ElasticSearch if requested.
        """
        #TODO: bypass_errors? probably just use self.config.bypass_errors

        logger.info("loading pages in target...")
        pages = self.target.load_pages()
        logger.info("... done loading pages in target")

        # Set up context that gets passed to several build/render functions
        # as well as filters
        context = {
            "current_time": time.strftime(self.config["time_format"]), # Get time once only
            "config": self.config,
            "mode": self.mode,
            "target": self.target.data, # just data, for legacy compat
            "pages": [p.data for p in pages], # just data, for legacy compat
            "categories": self.target.categories(),
        }

        es_data = {}
        matched_only = False
        for page in pages:
            if only_page:
                if match_only_page(only_page, currentpage):
                    matched_only = True
                else:
                    logger.debug("only_page mode: skipping page %s" % currentpage)
                    continue

            page_context = {currentpage=page.data, **context}

            if self.mode == "es" or es_upload != NO_ES_UP:
                es_template = self.template_for_page(page, mode="es")
                es_json_s = page.es_json(template, page_context)
                es_page_id = target.name+"."+page.data["html"]
                es_data[es_page_id] = es_json_s

            if self.mode == "html" or self.mode == "pdf":
                use_template = self.template_for_page(page)
                logger.debug("use_template is: %s" % use_template)
                page_text = page.render(use_template, page_context)
            elif self.mode == "md":
                if "md" not in page.data and "__md_generator" not in page.data:
                    logger.info("... md mode: Skipping page (no md): %s" % currentpage)
                    continue
                page_text = page.md_content(page_context)
            elif self.mode == "es":
                page_text = es_json_s
            else:
                exit("build_all() error: unknown mode: %s" % self.mode)

            if page_text:
                self.write_page(page_text, page.filepath(self.mode))
            else:
                logger.warning("not writing empty page '%s'"%page.data["name"])

        if es_upload != NO_ES_UP:
            self.upload_es(es_data)

        if only_page and not matched_only:
            exit("Didn't find requested 'only' page '%s'" % only_page)



    def template_for_page(self, page, mode=None):
        """
        Return the preferred template for the given page and mode, based on
        inherited settings from the page/target and global default.
        """
        if mode is None:
            mode = self.mode

        fieldname, default_template = {
            "html": ("template", self.default_html_template),
            "pdf": ("pdf_template", self.default_pdf_template),
            "es": ("es_template", self.default_es_template),
            "md": (None, None) # Markdown doesn't use a template
        }[mode]

        if fieldname in page.data:
            return self.get_template(page.data[fieldname])
        else:
            return default_template

    def write_page(self, page_text, filepath):
        # Join folders from filepath and out_path
        out_folder = os.path.join(self.out_path, os.path.dirname(filepath))
        if not os.path.isdir(out_folder):
            logger.info("creating output folder %s" % out_folder)
            os.makedirs(out_folder)
        fileout = os.path.join(out_path, filepath)
        with open(fileout, "w", encoding="utf-8") as f:
            logger.info("writing to file: %s..." % fileout)
            f.write(page_text)

    def watch(self):
        """
        replacement for:
        watch(mode, target, cli_args.only, cli_args.pdf,
                es_upload=cli_args.es_upload,)
        """
        #TODO: stub

    def copy_static(self, template_static=None, content_static=None, out_path=None):
        """
        Copy static files to the output directory.
        """

        if template_static is None:
            template_static = self.copy_template_static
        if content_static is None:
            content_static = self.copy_content_static
        if out_path is None:
            out_path = self.config["out_path"]

        if template_static:
            template_static_src = self.config["template_static_path"]

            if os.path.isdir(template_static_src):
                template_static_dst = os.path.join(out_path,
                                           os.path.basename(template_static_src))
                copy_tree(template_static_src, template_static_dst)
            else:
                logger.warning(("Template static path '%s' doesn't exist; "+
                                "skipping.") % template_static_src)

        if content_static:
            if "content_static_path" in self.config:
                if type(self.config["content_static_path"]) == str:
                    content_static_srcs = [self.config["content_static_path"]]
                else:
                    content_static_srcs = self.config["content_static_path"]

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


    def setup_html_env(self):
        """
        Set up a Jinja env to load custom templates for HTML / HTML->PDF builds.
        """
        if self.strict_undefined:
            preferred_undefined = jinja2.StrictUndefined
        else:
            preferred_undefined = jinja2.Undefined
        if "template_path" in self.config:
            env = jinja2.Environment(undefined=preferred_undefined,
                    loader=jinja2.FileSystemLoader(self.config["template_path"]))
        else:
            env = setup_fallback_env()

        # Customize env: add custom tests, lstrip & trim blocks
        def defined_and_equalto(a,b):
            return env.tests["defined"](a) and env.tests["equalto"](a, b)
        env.tests["defined_and_equalto"] = defined_and_equalto
        def undefined_or_ne(a,b):
            return env.tests["undefined"](a) or env.tests["ne"](a, b)
        env.tests["undefined_or_ne"] = undefined_or_ne

        env.lstrip_blocks = True
        env.trim_blocks = True
        self.html_env = env
        return env

    def setup_fallback_env(self):
        """
        Set up a Jinja env to load templates from the Dactyl package. These
        templates assume that we're not using StrictUndefined.
        """
        env = jinja2.Environment(loader=jinja2.PackageLoader(__name__))
        env.lstrip_blocks = True
        env.trim_blocks = True
        self.fallback_env = env
        return env

    def get_template(self, template_name):
        """
        Gets the named Jinja template from the user-specified template folder,
        and falls back to the Dactyl built-in templates if it doesn't.
        """
        # Nevermind - these should always be filled in during __init__
        # if self.html_env is None:
        #     self.setup_html_env()
        # if self.fallback_env is None:
        #     self.setup_fallback_env()

        try:
            t = self.html_env.get_template(template_name)
        except jinja2.exceptions.TemplateNotFound:
            logger.warning("falling back to Dactyl built-ins for template %s" % template_name)
            t = self.fallback_env.get_template(template_name)
        return t

    def get_es_template(self, filename):
        """
        Loads an ElasticSearch template (as JSON)
        """
        template_path = os.path.join(self.config["template_path"], filename)
        try:
            with open(template_path, encoding="utf-8") as f:
                es_template = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            if type(e) == FileNotFoundError:
                logger.debug("Didn't find ES template (%s), falling back to default" %
                    template_path)
            elif type(e) == json.decoder.JSONDecodeError:
                recoverable_error(("Error JSON-decoding ES template (%s)" %
                    template_path), self.bypass_errors)
            with resource_stream(__name__, BUILTIN_ES_TEMPLATE) as f:
                es_template = json.load(f)
        return es_template


########### TODO: cleanup
def add_bonus_fields(currentpage, target=None, pages=None, categories=[],
        mode="html", current_time="", bypass_errors=False):
    #TODO: move this to page or target, make this default in all modes?
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

    if config["preprocessor_allow_undefined"] == False and not bypass_errors:
        strict_undefined = True
    else:
        strict_undefined = False
    es_env = setup_pp_env(no_loader=True, strict_undefined=strict_undefined)

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
    args = [config["prince_executable"], '--javascript', '-o', abs_pdf_path, '--no-warn-css']

    pages = get_pages(target, bypass_errors)
    if only_page:
        pages = [p for p in pages if match_only_page(only_page, p)][:1]
        if not len(pages):
            recoverable_error("Couldn't find 'only' page %s" % only_page,
                bypass_errors)
            return
    # Each HTML output file in the target is another arg to prince
    args += [p["html"] for p in pages]

    # Change dir to the tempfiles path; this may avoid a bug in Prince
    old_cwd = os.getcwd()
    os.chdir(temp_files_path)

    logger.info("generating PDF: running %s..." % " ".join(args))
    prince_resp = subprocess.check_output(args, universal_newlines=True)
    print(prince_resp)

    # Clean up the tempdir now that we're done using it
    os.chdir(old_cwd)
    if remove_tmp:
        remove_tree(temp_files_path)


################ theoretically below here is OK?

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
        target = DactylTarget(config, inpages=cli_args.pages)
    elif cli_args.openapi:
        target = DactylTarget(config, spec_path=cli_args.openapi)
    else:
        target = DactylTarget(config, name=cli_args.target)

    if cli_args.vars:
        try:
            if cli_args.vars[-5:] in (".json",".yaml"):
                with open(cli_args.vars, "r", encoding="utf-8") as f:
                    custom_keys = yaml.load(f)
            else:
                custom_keys = yaml.load(cli_args.vars)
            target.gain_fields(custom_keys)
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            exit("FATAL: --vars value was improperly formatted: %s" % repr(e))

    if cli_args.title:
        target.gain_keys({"display_name": cli_args.title})

    if not cli_args.no_cover and not target.data.get("no_cover", False):
        target.add_cover()

    if cli_args.pdf != NO_PDF:
        mode = "pdf"
    elif cli_args.md:
        mode = "md"
    elif cli_args.es:
        mode = "es"
    else:
        mode = "html"

    builder = DactylBuilder(target, mode)

    if mode == "pdf":
        builder.pdf_filename = cli_args.pdf
    if mode == "es" or cli_args.es_upload:
        builder.es_upload = cli_args.es_upload

    # Override static files copy setting based on CLI flags, if any are used
    if cli_args.no_static:
        builder.copy_content_static = False
        builder.copy_template_static = False
    elif cli_args.template_static:
        builder.copy_content_static = False
        builder.copy_template_static = True
    elif cli_args.content_static:
        builder.copy_content_static = True
        builder.copy_template_static = False
    elif cli_args.copy_static:
        builder.copy_content_static = True
        builder.copy_template_static = True

    if cli_args.leave_temp_files:
        builder.leave_temp_files = True

    logger.info("loading pages..." % mode)
    builder.load()
    if cli_args.only:
        logger.info("building page %s..."%cli_args.only)
        builder.build_one(cli_args.only)
    else:
        logger.info("building target %s..."%target.name)
        builder.build_all()
    logger.info("done building")

    builder.copy_static()

    if cli_args.watch:
        logger.info("watching for changes...")
        builder.watch()


def dispatch_main():
    cli = DactylCLIParser(DactylCLIParser.UTIL_BUILD)
    global config
    config = DactylConfig(cli.cli_args)
    config.load_build_options()
    main(cli.cli_args)


if __name__ == "__main__":
    dispatch_main()
