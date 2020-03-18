################################################################################
## Dactyl Page Class
##
## A single HTML file in the output,
## or a placeholder for several
################################################################################

import jinja2
import requests

from markdown import markdown
from bs4 import BeautifulSoup

from dactyl.jinja_loaders import FrontMatterRemoteLoader, FrontMatterFSLoader
from dactyl.target import DactylTarget

class Page:
    def __init__(self, target, data):
        assert isinstance(target, DactylTarget)
        self.target = target
        self.config = self.target.config
        self.data = data
        self.rawtext = None
        self.pp_template = None

    def load(self, preprocess=True):
        """
        Load frontmatter and raw file contents without parsing or rendering.
        Does not return anything because rendering may depend on Jinja loading
        the page as a template, etc.
        """
        if "md" in self.data:
            if (self.data["md"][:5] == "http:" or
                    self.data["md"][:6] == "https:"):
                self.load_from_url(preprocess)
            else:
                self.load_from_disk(preprocess)
        elif "__md_generator" in self.data:
            self.load_from_generator(preprocess)


    def get_pp_env(self, loader):
        if (self.config["preprocessor_allow_undefined"] or
                self.config.bypass_errors):
            preferred_undefined = jinja2.Undefined
        else:
            preferred_undefined = jinja2.StrictUndefined

        pp_env = jinja2.Environment(undefined=preferred_undefined,
                loader=loader)

        # Add custom "defined_and_" tests
        def defined_and_equalto(a,b):
            return pp_env.tests["defined"](a) and pp_env.tests["equalto"](a, b)
        pp_env.tests["defined_and_equalto"] = defined_and_equalto
        def undefined_or_ne(a,b):
            return pp_env.tests["undefined"](a) or pp_env.tests["ne"](a, b)
        pp_env.tests["undefined_or_ne"] = undefined_or_ne

        # Pull exported values (& functions) from page filters into the pp_env
        for filter_name in self.filters():
            if filter_name not in self.config.filters.keys():
                logger.debug("Skipping unloaded filter '%s'" % filter_name)
                continue
            if "export" in dir(self.config.filters[filter_name]):
                for key,val in self.config.filters[filter_name].export.items():
                    logger.debug("... pulling in filter_%s's exported key '%s'"
                            % (filter_name, key))
                    pp_env.globals[key] = val

        return pp_env

    def load_from_url(self, preprocess):
        url = self.data["md"]
        assert (url[:5] == "http:" or url[:6] == "https:")
        if preprocess:
            pp_env = self.get_pp_env(loader=FrontMatterRemoteLoader())
            self.pp_template = pp_env.get_template(page["md"])
        else:
            response = requests.get(url)
            if response.status_code == 200:
                self.rawtext = response.text
            else:
                raise requests.RequestException("Status code for page was not 200")

    def load_from_disk(self, preprocess):
        """
        Read the file from the filesystem,
        as either raw text or a jinja template
        """
        if preprocess:
            path = self.config["content_path"]
            pp_env = self.get_pp_env(loader=FrontMatterFSLoader(path))
            self.pp_template = pp_env.get_template(self.data["md"])
        else:
            with open(self.data["md"], "r", encoding="utf-8") as f:
                self.rawtext = f.read()


    def load_from_generator(self, preprocess):
        """
        Load the text from a generator function,
        as either raw text or a jinja template
        """
        if preprocess:
            pp_env = self.get_pp_env(
                loader=jinja2.DictLoader({"_": self.data["__md_generator"]()}) )
            self.pp_template = pp_env.get_template("_")
        else:
            self.rawtext = self.data["__md_generator"]()

    ### TODO: figure out if this no_loader setup is still necessary
    # logger.debug("Using a no-loader Jinja environment")
    # pp_env = jinja2.Environment(undefined=preferred_undefined)

    def preprocess(self, context):
        md = self.pp_template.render(**context)
        # Apply markdown-based filters here
        for filter_name in self.filters():
            if "filter_markdown" in dir(self.config.filters[filter_name]):
                logger.info("... applying markdown filter %s" % filter_name)
                md = self.config.filters[filter_name].filter_markdown(
                    md,
                    logger=logger,
                    **context,
                )

        logger.info("... markdown is ready")
        return md

    def md_content(self, context={}):
        if self.rawtext is not None:
            return self.rawtext
        elif self.pp_template is not None:
            return self.preprocess(context)
        else:
            logger.warning("md_content(): no rawtext or pp_template")
            return ""

    def html_content(self, context={}):
        """
        Parse this page's markdown into HTML
        """

        md = self.md_content(context)

        logger.info("... parsing markdown...")
        html = markdown(md, extensions=["markdown.extensions.extra",
                                        "markdown.extensions.toc"],
                                        #TODO: scrap toc, make our own
                        lazy_ol=False)

        # Apply raw-HTML-string-based filters here
        for filter_name in self.filters():
            if "filter_html" in dir(self.config.filters[filter_name]):
                logger.info("... applying HTML filter %s" % filter_name)
                html = self.config.filters[filter_name].filter_html(
                        html,
                        logger=logger,
                        **context,
                )

        # Some filters would rather operate on a soup than a string.
        # May as well parse once and re-serialize once.
        soup = BeautifulSoup(html, "html.parser")

        # Apply soup-based filters here
        for filter_name in self.filters():
            if "filter_soup" in dir(config.filters[filter_name]):
                logger.info("... applying soup filter %s" % filter_name)
                self.config.filters[filter_name].filter_soup(
                        soup,
                        logger=logger,
                        **context,
                )
                # ^ the soup filters apply to the same object, passed by reference

        logger.info("... re-rendering HTML from soup...")
        html2 = str(soup)
        return html2

    def filters(self):
        """
        Returns the names of filters to use when processing this page.
        """
        ffp = set(self.config["default_filters"])
        # can skip this step, since "filters" is inherited by page anyway
        # if "filters" in self.target.data:
        #     ffp.update(self.target.data["filters"])
        if "filters" in self.data:
            ffp.update(self.data["filters"])
        loaded_filters = set(self.config.filters.keys())
        # logger.debug("Removing unloaded filters from page %s...\n  Before: %s"%(page,ffp))
        ffp &= loaded_filters
        # logger.debug("  After: %s"%ffp)
        return ffp
