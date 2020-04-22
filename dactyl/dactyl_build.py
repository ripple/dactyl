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

from watchdog.observers import Observer

from dactyl.config import DactylConfig
from dactyl.cli import DactylCLIParser
from dactyl.target import DactylTarget
from dactyl.page import DactylPage
from dactyl.watch_handler import UpdaterHandler



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
            self.staging_folder = self.temp_dir()
            self.pdf_filename = PDF_USE_DEFAULT

        self.leave_temp_files = False

        if mode == "es":
            self.es_upload = ES_USE_DEFAULT
        else:
            self.es_upload = NO_ES_UP

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
    def match_only_page(only_page, currentpage_data):
        """
        Returns a boolean indicating whether currentpage (object) matches the
        only_page parameter (string). Used for build_one()
        """
        if not only_page:
            return False
        if only_page[-5:] == ".html":
            if (currentpage_data["html"] == only_page or
                    os.path.basename(currentpage_data["html"]) == only_page):
                return True
        elif only_page[-3:] == ".md":
            if "md" in currentpage_data and (currentpage_data["md"] == only_page or
                    os.path.basename(currentpage_data["md"]) == only_page):
                return True
        return False

    def build_all(self, only_page=None):
        """
        Build and write all pages in the target, according to the set mode,
        and upload their entries to ElasticSearch if requested.
        """

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
                if self.match_only_page(only_page, page.data):
                    matched_only = True
                else:
                    logger.debug("only_page mode: skipping page %s" % page)
                    continue

            page_context = {"currentpage":page.data, **context}

            if self.mode == "es" or self.es_upload != NO_ES_UP:
                es_template = self.template_for_page(page, mode="es")
                es_json_s = page.es_json(es_template, page_context)
                es_page_id = self.target.name+"."+page.data["html"]
                es_data[es_page_id] = es_json_s

            if self.mode == "html" or self.mode == "pdf":
                use_template = self.template_for_page(page)
                logger.debug("use_template is: %s" % use_template)
                page_text = page.render(use_template, page_context)
            elif self.mode == "md":
                if "md" not in page.data and "__md_generator" not in page.data:
                    logger.info("... md mode: Skipping page (no md): %s" % page)
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

        if only_page and not matched_only:
            exit("Didn't find requested 'only' page '%s'" % only_page)

        if self.es_upload != NO_ES_UP:
            self.upload_es(es_data)

        if self.mode == "pdf":
            self.assemble_pdf(only_page)


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
        """
        Writes HTML/MD/ES JSON out to the filesystem.
        """
        if self.mode == "pdf":
            # only the final pdf goes to out_path
            base_folder = self.staging_folder
        else:
            base_folder = self.out_path

        # Join folders in case the filepath is not just a flat file
        out_folder = os.path.join(base_folder, os.path.dirname(filepath))
        if not os.path.isdir(out_folder):
            logger.info("creating output folder %s" % out_folder)
            os.makedirs(out_folder)
        fileout = os.path.join(base_folder, filepath)
        with open(fileout, "w", encoding="utf-8") as f:
            logger.info("writing to file: %s..." % fileout)
            f.write(page_text)

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
                    extensions=['jinja2.ext.i18n'],
                    loader=jinja2.FileSystemLoader(self.config["template_path"]))
        else:
            env = self.setup_fallback_env()

        # Customize env: add custom tests, lstrip & trim blocks
        def defined_and_equalto(a,b):
            return env.tests["defined"](a) and env.tests["equalto"](a, b)
        env.tests["defined_and_equalto"] = defined_and_equalto
        def undefined_or_ne(a,b):
            return env.tests["undefined"](a) or env.tests["ne"](a, b)
        env.tests["undefined_or_ne"] = undefined_or_ne

        env.lstrip_blocks = True
        env.trim_blocks = True

        # Set up internationalization
        mo_file = self.target.data.get("locale_file", None)
        if mo_file:
            logger.debug("Loading strings from locale_file %s"%mo_file)
            try:
                with open(mo_file, "rb") as f:
                    tl = gettext.GNUTranslations(f)
                # TODO: add_fallback?? maybe a general config option there...
            except Exception as e:
                recoverable_error("Failed to load locale_file %s: %s" %
                                  (mo_file, e), self.config.bypass_errors,
                                  error=e)
                tl = gettext.NullTranslations()
        else:
            logger.debug("No locale_file setting found.")
            tl = gettext.NullTranslations()
        env.install_gettext_translations(tl, newstyle=True)
        # env.install_gettext_callables(gettext.gettext, gettext.ngettext, newstyle=True)


        self.html_env = env
        return env

    def setup_fallback_env(self):
        """
        Set up a Jinja env to load templates from the Dactyl package. These
        templates assume that we're not using StrictUndefined.
        """
        env = jinja2.Environment(loader=jinja2.PackageLoader(__name__),
                                 extensions=['jinja2.ext.i18n'])
        env.lstrip_blocks = True
        env.trim_blocks = True
        self.fallback_env = env
        # env.install_gettext_callables(gettext.gettext, gettext.ngettext, newstyle=True)
        return env

    def get_template(self, template_name):
        """
        Gets the named Jinja template from the user-specified template folder,
        and falls back to the Dactyl built-in templates if it doesn't.
        """

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
        try:
            template_path = os.path.join(self.config["template_path"], filename)
            with open(template_path, encoding="utf-8") as f:
                es_template = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError, KeyError) as e:
            if type(e) == FileNotFoundError:
                logger.debug("Didn't find ES template (%s), falling back to default" %
                    template_path)
            elif type(e) == json.decoder.JSONDecodeError:
                recoverable_error(("Error JSON-decoding ES template (%s)" %
                    template_path), self.config.bypass_errors,
                    error=e)
            elif type(e) == KeyError:
                logger.debug("template_path isn't defined. No config file?")
            with resource_stream(__name__, BUILTIN_ES_TEMPLATE) as f:
                es_template = json.load(f)
        return es_template

    def upload_es(self, data):
        """
        Upload to ElasticSearch. data is a dict mapping page IDs to JSON strings
        """
        es_base = self.cleanup_es_url()
        es_index = self.target.es_index_name()

        for id, json_s in data.values():
            doc_type="article"## TODO: other options?

            url = "{es_base}/{index}/{doc_type}/{id}".format(
                es_base=es_base,
                index=es_index.lower(), # ES index names must be lowercase
                doc_type=doc_type,
                id=id,
            )
            headers = {"Content-Type": "application/json"}
            logger.info("Uploading to ES: PUT %s" % url)
            r = requests.put(url, headers=headers, data=json_s)
            if r.status_code >= 400:
                recoverable_error("ES upload failed with error: '%s'" % r.text,
                        self.config.bypass_errors)

    def cleanup_es_url(self):
        """
        Do some post-processing on user-specified ES URLs to clean them up,
        or supply a default ES URL if one wasn't provided.
        """
        # Should not be called if not doing es upload
        assert self.es_upload != NO_ES_UP

        if self.es_upload == ES_USE_DEFAULT:
            es_base_url = self.config.get("elasticsearch", "http://localhost:9200")
        else:
            # URL was explicitly specified
            es_base_url = self.es_upload

        # Make sure it has an http:// or https:// prefix
        if es_base_url[:7] != "http://" and es_base_url[:8] != "https://":
            es_base_url = "https://"+es_base_url

        if es_base_url[-1] == "/": # Drop trailing slash
            es_base_url = es_base_url[:-1]

        logger.debug("ElasticSearch base URL is '%s'" % es_base_url)
        return es_base_url

    def assemble_pdf(self, only_page=None):
        """
        Use Prince to combine temporary HTML files into a PDF.
        Called at the end of build_all()
        """
        assert self.pdf_filename != NO_PDF

        if self.pdf_filename == PDF_USE_DEFAULT:
            # Not sure if this can change in watch mode
            pdf_filename = self.target.default_pdf_name()
        else:
            pdf_filename = self.pdf_filename

        # self.staging_folder should contain HTML files by now. Copy static
        # files there too, since Prince will need them
        self.copy_static(True, True, out_path=self.staging_folder)

        # Make sure the path we're going to write the PDF to exists
        if not os.path.isdir(self.out_path):
            logger.info("creating output folder %s" % self.out_path)
            os.makedirs(self.out_path)
        abs_pdf_path = os.path.abspath(os.path.join(self.out_path, pdf_filename))

        # Start preparing the prince command
        args = [self.config["prince_executable"], '--javascript', '-o', abs_pdf_path, '--no-warn-css']

        pages = self.target.pages
        if only_page:
            pages = [p for p in pages if self.match_only_page(only_page, p.data)][:1]
            if not len(pages):
                recoverable_error("Couldn't find 'only' page %s" % only_page,
                    self.config.bypass_errors)
                return
        # Each HTML output file in the target is another arg to prince
        args += [p.data["html"] for p in pages]

        # Change dir to the tempfiles path; this may avoid a bug in Prince
        old_cwd = os.getcwd()
        os.chdir(self.staging_folder)

        logger.info("generating PDF: running %s..." % " ".join(args))
        prince_resp = subprocess.check_output(args, universal_newlines=True)
        print(prince_resp)

        # Clean up the staging_folder now that we're done using it
        os.chdir(old_cwd)
        if not self.leave_temp_files:
            remove_tree(self.staging_folder)


    def watch(self):
        """
        Look for changed files and re-run the build whenever there's an update.
        Runs until interrupted.

        replacement for:
        watch(mode, target, cli_args.only, cli_args.pdf,
                es_upload=cli_args.es_upload,)
        """

        event_handler = UpdaterHandler(builder=self)
        observer = Observer()
        observer.schedule(event_handler, self.config["template_path"], recursive=True)
        observer.schedule(event_handler, self.config["content_path"], recursive=True)
        observer.start()
        # The above starts an observing thread,
        #   so the main thread can just wait
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

def list_targets(config):
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

def main(cli_args, config):
    if cli_args.list_targets_only:
        list_targets(config)
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

    builder = DactylBuilder(target, config, mode)

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
    config = DactylConfig(cli.cli_args)
    config.load_build_options()
    main(cli.cli_args, config)


if __name__ == "__main__":
    dispatch_main()
