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

class DactylPage:
    def __init__(self, target, data):
        assert isinstance(target, DactylTarget)
        self.target = target
        self.config = self.target.config
        self.data = data
        self.rawtext = None
        self.pp_template = None
        self.toc = []

    def load(self, preprocess=True):
        """
        Load frontmatter and raw file contents without parsing or rendering.
        Does not return anything because rendering may depend on Jinja loading
        the page as a template, etc.
        """
        logger.info("Preparing page %s" % self.data)
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
        logger.info("Loading page from URL: %s"%url)
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
            logger.info("... loading markdown from filesystem")
            path = self.config["content_path"]
            pp_env = self.get_pp_env(loader=FrontMatterFSLoader(path))
            self.pp_template = pp_env.get_template(self.data["md"])
        else:
            logger.info("... reading markdown from file")
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
        ## Context:
            # target=target,
            # categories=categories,
            # mode=mode,
            # current_time=current_time,
            # page_filters=page_filters,
            # bypass_errors=bypass_errors
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
        Returns the page's contents as HTML. Parses Markdown & runs filters
        if any.
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
                ## Context:
                    # html,
                    # currentpage=page,
                    # categories=categories,
                    # pages=pages,
                    # target=target,
                    # current_time=current_time,
                    # mode=mode,
                    # config=config,
                    # logger=logger,
                html = self.config.filters[filter_name].filter_html(
                        html,
                        logger=logger,
                        **context,
                )

        # Some filters would rather operate on a soup than a string.
        # May as well parse once and re-serialize once.
        soup = BeautifulSoup(html, "html.parser")

        # Give each header a unique ID and fill out the Table of Contents
        self.update_toc(soup)

        # Apply soup-based filters here
        for filter_name in self.filters():
            if "filter_soup" in dir(config.filters[filter_name]):
                logger.info("... applying soup filter %s" % filter_name)
                ## Context:
                    # soup,
                    # currentpage=page,
                    # categories=categories,
                    # pages=pages,
                    # target=target,
                    # current_time=current_time,
                    # mode=mode,
                    # config=config,
                    # logger=logger,
                self.config.filters[filter_name].filter_soup(
                        soup,
                        logger=logger,
                        **context,
                )
                # ^ the soup filters apply to the same object, passed by reference

        logger.info("... re-rendering HTML from soup...")
        html2 = str(soup)
        return html2

    @staticmethod
    def idify(utext):
        """Make a string ID-friendly (but more unicode-friendly)"""
        utext = re.sub(r'[^\w\s-]', '', utext).strip().lower()
        utext = re.sub(r'[\s-]+', '-', utext)
        if not len(utext):
            # Headers must be non-empty
            return '_'
        return utext

    def update_toc(self, soup):
        """
        Assign unique IDs to header elements in a BeautifulSoup object, and
        update internal table of contents accordingly.
        The resulting ToC is a list of objects, each in the form:
        {
            "text": "Header Content as Text",
            "id": "header-content-as-text", # doesn't have the # prefix
            "level": 1, #1-6, based on h1, h2, etc.
        }
        """

        self.toc = []
        uniqIDs = {}
        headers = soup.find_all(name=re.compile("h[1-6]"))
        for h in headers:
            h_id = self.idify(h.get_text())
            if h_id not in uniqIDs.keys():
                uniqIDs[h_id] = 0
            else:
                # not unique, append -1, -2, etc. to this instance
                uniqIDs[h_id] += 1
                h_id = "{id}-{n}".format(id=h_id, n=uniqIDs[h_id])

            h["id"] = h_id
            self.toc.append({
                "text": h.get_text(),
                "id": h_id,
                "level": int(h.name[1])
            })

    def legacy_toc(self):
        """
        Return an HTML table of contents in the legacy format from the internal
        table of contents list.
        """
        soup = BeautifulSoup("", "html.parser")
        for h in self.toc:
            a = soup.new_tag("a", href="#"+h["id"])
            a.string = h["text"]
            li = soup.new_tag("li")
            li["class"] = "level-{n}".format(n=h["level"])
            li.append(a)
            soup.append(li)
        return str(soup)



    def render(self, use_template, context):
        """
        Render the entire page using the given template & context.
        """
        ## Context:
            # currentpage=currentpage, ## - probably remove
            # categories=categories,
            # pages=pages,
            # content=html_content, ## remove
            # target=target,
            # current_time=current_time,
            # page_toc=page_toc, ## remove
            # sidebar_content=page_toc, ## remove
            # mode=mode,
            # config=config
        # TODO: try block around html_content()?
        html_content = self.html_content(context)
        page_toc = self.toc_from_headers()#TODO

        out_html = use_template.render(
            currentpage=currentpage.data, #TODO?
            content=html_content,
            sidebar_content=self.legacy_toc(),
            page_toc=self.legacy_toc(),
            headers=self.toc,
            **context,
        )


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
