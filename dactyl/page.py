################################################################################
## Dactyl Page Class
##
## Handles the loading, default values, preprocessing, and content parsing
## for a single HTML page of output.
################################################################################

import jinja2
import requests

from markdown import markdown
from bs4 import BeautifulSoup

from dactyl.common import *

from dactyl.jinja_loaders import FrontMatterRemoteLoader, FrontMatterFSLoader

class DactylPage:
    def __init__(self, config, data, skip_pp=False, more_filters=[]):
        self.config = config
        self.data = data
        self.rawtext = None
        self.pp_template = None
        self.twolines = None
        self.toc = []
        self.ffp = None
        self.skip_pp = skip_pp
        self.md = None
        self.html = None
        self.soup = None

        self.gain_filters(more_filters)
        self.load_content()
        self.provide_default_filename()
        self.provide_name()
        # self.html_content({"currentpage":data, **context})

    def get_pp_env(self, loader):
        if (self.config["preprocessor_allow_undefined"] or
                self.config.bypass_errors):
            preferred_undefined = jinja2.Undefined
        else:
            preferred_undefined = jinja2.StrictUndefined

        pp_env = jinja2.Environment(undefined=preferred_undefined,
                extensions=['jinja2.ext.i18n'], loader=loader)

        # Add custom "defined_and_" tests
        def defined_and_equalto(a,b):
            return pp_env.tests["defined"](a) and pp_env.tests["equalto"](a, b)
        pp_env.tests["defined_and_equalto"] = defined_and_equalto
        def undefined_or_ne(a,b):
            return pp_env.tests["undefined"](a) or pp_env.tests["ne"](a, b)
        pp_env.tests["undefined_or_ne"] = undefined_or_ne

        # Pull exported values (& functions) from page filters into the pp_env
        for filter_name in self.filters(save=False):
            if filter_name not in self.config.filters.keys():
                logger.debug("Skipping unloaded filter '%s'" % filter_name)
                continue
            if "export" in dir(self.config.filters[filter_name]):
                for key,val in self.config.filters[filter_name].export.items():
                    logger.debug("... pulling in filter_%s's exported key '%s'"
                            % (filter_name, key))
                    pp_env.globals[key] = val

        return pp_env

    def load_content(self):
        """
        Dispatcher for loading this page's content based on the "md" field.
        """
        logger.debug("Loading page %s" % self)
        if "md" in self.data:
            if (self.data["md"][:5] == "http:" or
                    self.data["md"][:6] == "https:"):
                self.load_from_url()
            else:
                self.load_from_disk()
        elif "__md_generator" in self.data:
            self.load_from_generator()

    def load_from_url(self):
        """
        Read file over HTTP(S),
        as either raw text or as a Jinja template,
        and load frontmatter, if any, either way.
        """
        url = self.data["md"]
        logger.info("Loading page from URL: %s"%url)
        assert (url[:5] == "http:" or url[:6] == "https:")
        if not self.skip_pp:
            pp_env = self.get_pp_env(loader=FrontMatterRemoteLoader())
            self.pp_template = pp_env.get_template(self.data["md"])
            frontmatter = pp_env.loader.fm_map[self.data["md"]]
            merge_dicts(frontmatter, self.data)
            # special case: let frontmatter overwrite default "html" vals
            if PROVIDED_FILENAME_KEY in self.data and "html" in frontmatter:
                self.data["html"] = frontmatter["html"]
            self.twolines = pp_env.loader.twolines[self.data["md"]]
        else:
            response = requests.get(url)
            if response.status_code == 200:
                self.rawtext, frontmatter = parse_frontmatter(response.text)
                merge_dicts(frontmatter, self.data)
                # special case: let frontmatter overwrite default "html" vals
                if PROVIDED_FILENAME_KEY in self.data and "html" in frontmatter:
                    self.data["html"] = frontmatter["html"]
                self.twolines = self.rawtext.split("\n", 2)[:2]
            else:
                raise requests.RequestException("Status code for page was not 200")

    def load_from_disk(self):
        """
        Read the file from the filesystem,
        as either raw text or as a Jinja template,
        and load frontmatter, if any, either way.
        """
        assert "md" in self.data
        if not self.skip_pp:
            logger.debug("... loading markdown from filesystem")
            path = self.config["content_path"]
            pp_env = self.get_pp_env(loader=FrontMatterFSLoader(path))
            self.pp_template = pp_env.get_template(self.data["md"])
            frontmatter = pp_env.loader.fm_map[self.data["md"]]
            merge_dicts(frontmatter, self.data)
            # special case: let frontmatter overwrite default "html" vals
            if PROVIDED_FILENAME_KEY in self.data and "html" in frontmatter:
                self.data["html"] = frontmatter["html"]
            self.twolines = pp_env.loader.twolines[self.data["md"]]
        else:
            logger.info("... reading markdown from file")
            fullpath = os.path.join(self.config["content_path"], self.data["md"])
            with open(fullpath, "r", encoding="utf-8") as f:
                ftext = f.read()
            self.rawtext, frontmatter = parse_frontmatter(ftext)
            merge_dicts(frontmatter, self.data)
            # special case: let frontmatter overwrite default "html" vals
            if PROVIDED_FILENAME_KEY in self.data and "html" in frontmatter:
                self.data["html"] = frontmatter["html"]
            self.twolines = self.rawtext.split("\n", 2)[:2]


    def load_from_generator(self):
        """
        Load the text from a generator function,
        as either raw text or a jinja template.
        Assume no frontmatter in this case.
        """
        if not self.skip_pp:
            pp_env = self.get_pp_env(
                loader=jinja2.DictLoader({"_": self.data["__md_generator"]()}) )
            self.pp_template = pp_env.get_template("_")
        else:
            self.rawtext = self.data["__md_generator"]()

    def provide_default_filename(self):
        """
        Provide a default "html" filename to a page dictionary if one wasn't
        explicitly specified. Frontmatter can overwrite this value, but code
        won't see the frontmatter-provided "html" value when not building the
        target containing that page.
        """
        if "html" in self.data:
            return

        logger.debug("Need to generate html filename for page %s" % self)
        if "md" in self.data:
            # TODO: support other formulas including "tail" or "pretty"
            new_filename = re.sub(r"[.]md$", ".html", self.data["md"])
            if self.config.get("flatten_default_html_paths", True):
                new_filename = new_filename.replace(os.sep, "-")
            self.data["html"] = new_filename
        elif "name" in self.data:
            new_filename = slugify(self.data["name"]).lower()+".html"
            self.data["html"] = new_filename
        else:
            new_filename = str(time.time()).replace(".", "-")+".html"
            self.data["html"] = new_filename
        self.data[PROVIDED_FILENAME_KEY] = True

        logger.debug("Generated html filename '%s' for page: %s" %
                    (new_filename, self))

    def provide_name(self):
        """
        Add the "name" field, if not defined.
        """
        if "name" in self.data:
            return

        if "title" in self.data: # Port over the "title" attribute instead
            self.data["name"] = self.data["title"]
            logger.debug("Guessed page name from title for page %s" % self)
            return
        elif self.twolines:
            logger.debug("Guessing page name from first two lines...")
            try:
                soup = BeautifulSoup(markdown("\n".join(self.twolines)), "html.parser")
                first_h = soup.find(name=re.compile("h[1-6]"))
                self.data["name"] = first_h.get_text()
                logger.debug("... guessed title: '%s'"%self.data["name"])
                return
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                logger.warning(("Couldn't guess title of page '%s' from its "+
                                "first two lines:\n%s") % (self,
                                    "\n".join(self.twolines)))

        if "md" in self.data:
            self.data["name"] = self.data["md"]
            logger.debug("Using placeholder name for page based on md path: '%s'"%self.data["name"])
        else:
            logger.warning("Using a placeholder name for page %s" %
                    str(self.data))
            self.data["name"] = str(time.time()).replace(".", "-")



    def preprocess(self, context):
        try:
            md = self.pp_template.render(**context)
        except Exception as e:
            recoverable_error("Preprocessor error in page %s: %s."%(self, e),
                              self.config.bypass_errors, error=e)
            # Preprocessing failed. Skip this step and reload.
            self.skip_pp = True
            self.load_content()
            return self.md_content(context)
        # Apply markdown-based filters here
        for filter_name in self.filters():
            if "filter_markdown" in dir(self.config.filters[filter_name]):
                logger.info("... applying markdown filter %s" % filter_name)
                try:
                    md = self.config.filters[filter_name].filter_markdown(
                        md,
                        logger=logger,
                        **context,
                    )
                except Exception as e:
                    recoverable_error("Markdown filter '%s' failed on page %s: %s" %
                                  (filter_name, self, e),
                                  self.config.bypass_errors, error=e)

        logger.info("... markdown is ready")
        self.md = md
        return md

    def md_content(self, context):
        if self.md is not None:
            # return already-preprocessed md
            return self.md
        elif self.rawtext is not None:
            return self.rawtext
        elif not self.skip_pp and self.pp_template is not None:
            return self.preprocess(context)
        else:
            logger.debug("page %s has no rawtext or pp_template"%self.data)
            return ""

    def html_content(self, context, regen=False, save=True):
        """
        Returns the page's contents as HTML. Parses Markdown & runs filters
        if any.
        """
        if self.html is not None and not regen:
            # Reuse saved results if we have them
            return self.html

        md = self.md_content(context)

        logger.info("... parsing markdown...")
        html = markdown(md, extensions=["markdown.extensions.extra",
                                        "markdown.extensions.sane_lists"])

        # Apply raw-HTML-string-based filters here
        for filter_name in self.filters():
            if "filter_html" in dir(self.config.filters[filter_name]):
                logger.info("... applying HTML filter %s" % filter_name)
                try:
                    html = self.config.filters[filter_name].filter_html(
                            html,
                            logger=logger,
                            **context,
                    )
                except Exception as e:
                    recoverable_error("HTML filter '%s' failed on page %s: %s" %
                            (filter_name, self, e), self.config.bypass_errors,
                            error=e)

        # Some filters would rather operate on a soup than a string.
        # May as well parse once and re-serialize once.
        soup = BeautifulSoup(html, "html.parser")
        self.soup = soup

        # Give each header a unique ID and fill out the Table of Contents
        self.update_toc()

        # Add a "blurb" attribute to the page
        self.provide_blurb()

        # Add this page's plaintext field. ElasticSearch upload uses this.
        self.data["plaintext"] = soup.get_text()

        # Apply soup-based filters here
        for filter_name in self.filters():
            if "filter_soup" in dir(self.config.filters[filter_name]):
                logger.info("... applying soup filter %s" % filter_name)
                try:
                    self.config.filters[filter_name].filter_soup(
                            soup,
                            logger=logger,
                            **context,
                    )
                    # ^ the soup filters apply to the same object, passed by reference
                except Exception as e:
                    recoverable_error("Soup filter '%s' failed on page %s: %s" %
                                  (filter_name, self, e),
                                  self.config.bypass_errors, error=e)

        logger.info("... re-rendering HTML from soup...")
        html2 = str(soup)
        if save:
            self.html = html2
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

    def update_toc(self):
        """
        Assign unique IDs to header elements in a BeautifulSoup object, and
        update internal table of contents accordingly.
        The resulting ToC is a list of objects, each in the form:
        {
            "text": "Header Content as Text",
            "id": "header-content-as-text", # doesn't have the # prefix
            "level": 1, #1-6, based on h1, h2, etc.
        }
        Also add the "headermap" field used for ES JSON, which is in the form
        {
            "Header Content as Text": "#header-content-as-text"
        }
        """

        self.toc = []
        uniqIDs = {}
        headermap = {}
        headers = self.soup.find_all(name=re.compile("h[1-6]"))
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
            # ElasticSearch doesn't like dots in keys, so escape those
            escaped_name = h.get_text().replace(".","-")
            headermap[escaped_name] = "#"+h_id
        self.data["headermap"] = headermap

    def legacy_toc(self):
        """
        Return an HTML table of contents in the legacy format from the internal
        table of contents list.
        """
        soup = BeautifulSoup("", "html.parser")
        for h in self.toc:
            if h["level"] > 3:
                # legacy toc only goes down to h3
                continue
            a = soup.new_tag("a", href="#"+h["id"])
            a.string = h["text"]
            li = soup.new_tag("li")
            li["class"] = "level-{n}".format(n=h["level"])
            li.append(a)
            soup.append(li)
            soup.append("\n")
        return str(soup)

    def provide_blurb(self):
        """
        Add a "blurb" field, based on the first paragraph in the page, if one
        is not already provided.
        """
        if "blurb" in self.data:
            return
        p = self.soup.find("p")
        while p:
            if p.get_text().strip():
                self.data["blurb"] = p.get_text()
                break
            else:
                p = p.find_next_sibling("p")
        else:
            logger.debug("Couldn't find a paragraph with text in page %s." % self.data["name"])
            # No text? No blurb.
            self.data["blurb"] = ""

    def render(self, use_template, context):
        """
        Render the entire page using the given template & context.
        """
        # TODO: try block around html_content()?
        html_content = self.html_content(context)

        out_html = use_template.render(
            content=html_content,
            sidebar_content=self.legacy_toc(),
            page_toc=self.legacy_toc(),
            headers=self.toc,
            **context,
        )
        return out_html

    def es_json(self, use_template, context):
        """
        Return JSON for uploading to ElasticSearch
        """
        # Parse HTML to get the required "bonus" fields like blurb and toc, but
        # don't save the "es"-rendered HTML as the final output, in case this
        # is a build-HTML-and-upload-ES run.
        es_context = {**context}
        es_context["mode"] = "es"
        self.html_content(es_context, save=False)

        # Set up Jinja env for rendering strings
        es_env = self.get_pp_env(loader=None)#TODO: does this even work?

        def eval_es_string(expr):
            try:
                result = eval(expr, {}, context)
            except Exception as e:
                recoverable_error(
                    "__dactyl_eval__ failed on expression '{expr}': {e}".format(
                        expr=expr, e=e),
                    self.config.bypass_errors
                )
                result = expr
            return result

        def render_es_field(value):
            if type(value) == str: # jinja-render strings
                field_templ = es_env.from_string(value)
                try:
                    parsed_field = field_templ.render(context)
                except jinja2.exceptions.TemplateSyntaxError as e:
                    recoverable_error(
                        "Couldn't parse value '{value}' in ES template: {e}".format(
                            value, e),
                        self.config.bypass_errors
                    )
                return parsed_field
            elif type(value) in (type(None), int, float, bool): # preserve literals
                return value
            elif type(value) == dict and ES_EVAL_KEY in value.keys():
                return eval_es_string(value[ES_EVAL_KEY])
            elif type(value) == dict: # recurse!
                return {rkey: render_es_field(rval) for rkey,rval in value.items()}
            elif type(value) == list: # recurse!
                return [render_es_field(rval) for rval in value]
            else:
                recoverable_error("Unknown type '{t}' in ES template" % type(value))
                return ""

        wout = {key: render_es_field(val) for key,val in use_template.items()}
        return json.dumps(wout, indent=4, separators=(',', ': '))

    def filepath(self, mode):
        """
        Returns the preferred filename to write output to based on the provided
        mode.
        """

        if mode == "es":
            # use .json as file extension instead
            fp = re.sub(r'(.+)\.html?$', r'\1.json', self.data["html"], flags=re.I)
            if fp[-5:] != ".json": # substitution didn't work
                fp = fp+".json"
            return fp
        elif mode == "md":
            if "md" in self.data:
                # reuse the input .md filename as output
                fp = self.data["md"]
                if ":" in fp: # http: or https: probably
                    fp = slugify(f)
            else:
                # use the html field, but change the file extension to .md
                fp = re.sub(r'(.+)\.html?$', r'\1.md', self.data["html"], flags=re.I)
                if fp[-3:] != ".md": # substitution didn't work
                    fp = fp+".md"
            return fp
        else:
            # for pdf or html just use the html field as-is
            return self.data["html"]

    def gain_filters(self, filterlist):
        """
        Called by target to add its filters to this page's.
        """
        if "filters" in self.data:
            self.data["filters"] = filterlist + self.data["filters"]
        else:
            self.data["filters"] = filterlist

    def filters(self, save=True):
        """
        Returns the names of filters to use when processing this page.
        """
        if self.ffp:
            # Return saved results
            return self.ffp

        # Create de-duplicated list of loaded filters only
        ffp = []
        for f in self.config["default_filters"]:
            if f not in ffp and f in self.config.filters:
                ffp.append(f)
        for f in self.data.get("filters", [])    :
            if f not in ffp and f in self.config.filters:
                ffp.append(f)

        logger.debug("...filters for page: %s"%ffp)
        if save:
            self.ffp = ffp
        return ffp

    def __repr__(self):
        if "name" in self.data and "html" in self.data:
            return "<Page '{name}' ({html})>".format(
                name=self.data["name"],
                html=self.data["html"],
            )
        if "name" in self.data:
            return "<Page '{name}'>".format(name=self.data["name"])
        if "html" in self.data:
            return "<Page ({html})>".format(html=self.data["html"])
        strdata = str(self.data)
        if len(strdata) > 30:
            strdata = strdata[:27]+"..."
        return "<Page {{{strdata}}}>".format(strdata=strdata)
