################################################################################
## Dactyl Target Class
##
## Defines a group of pages that are built together.
################################################################################

from dactyl.common import *
from dactyl.config import DactylConfig
from dactyl.openapi import ApiDef

class DactylTarget:
    def __init__(self, config, name=None, inpages=None, spec_path=None):
        assert isinstance(config, DactylConfig)
        self.config = config
        self.pages = None

        # Set self.data based on the input type
        if inpages is not None:
            self.from_adhoc(inpages)
        elif spec_path is not None:
            self.from_openapi(spec_path)
        else:
            self.from_config(name)
        self.name = self.data["name"]


    def from_config(self, name=None):
        """
        Pick a target from the existing config file, by its short name.
        If no name is provided, use whichever target is listed first.
        """
        if name is None:
            if len(self.config["targets"]) == 0:
                logger.critical("No targets found. Either specify a config file or --pages")
                exit(1)
            self.data = self.config["targets"][0]
        else:
            try:
                self.data = next(t for t in self.config["targets"] if t["name"] == name)
            except StopIteration:
                logger.critical("Unknown target: %s" % target)
                exit(1)

    def from_adhoc(self, inpages):
        """
        Create an ad-hoc target from a list of input pages, generally passed as
        a list of files from the commandline.
        """
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
            self.config["content_path"] = in_dir

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
            self.config["pages"].append(new_page)

        self.data = t
        self.config["targets"].append(t)

    def from_openapi(spec_path):
        """
        Create a target from an API spec path.
        """

        openapi = ApiDef.from_path(spec_path)
        t = {
            "name": openapi.api_slug,
            "display_name": openapi.api_title,
        }

        self.config["pages"] = [{
            "openapi_specification": spec_path,
            "api_slug": openapi.api_slug,
            "targets": [openapi.api_slug],
        }]
        self.config["targets"].append(t)
        self.data = t

    def slug_name(self, fields_to_use=[], separator="-"):
        """Make a name for the target that's safe for use in URLs & filenames,
        from human-readable fields"""
        filename_segments = []
        for fieldname in fields_to_use:
            if fieldname in self.data.keys():
                filename_segments.append(slugify(self.data[fieldname]))

        if filename_segments:
            return separator.join(filename_segments)
        else:
            return slugify(self.name)

    def es_index_name(self):
        return self.slug_name(self.config["es_index_fields"],
                              self.config["es_index_separator"])

    def add_cover(self):
        """
        Add the default cover page to the pagelist where self.update_pages()
        will find it.
        """
        coverpage = self.config["cover_page"]
        coverpage["targets"] = [self.name]
        self.config["pages"].insert(0, coverpage)

    def default_pdf_name(self):
        """Choose a reasonable name for a PDF file in case one isn't specified."""
        return self.slug_name(self.config["pdf_filename_fields"],
                              self.config["pdf_filename_separator"]) + ".pdf"

    def error(self, msg, err=None):
        if err:
            traceback.print_tb(e.__traceback__)
            recoverable_error("{msg}: {err}".format(msg=msg, err=repr(e)),
                              self.config.bypass_errors)
        else:
            recoverable_error("msg, self.config.bypass_errors)

    def should_include(self, page):
        """Report whether a given page should be part of this target"""
        if "targets" not in page:
            return False
        if self.name in page["targets"]:
            return True
        else:
            return False

    def gain_fields(self, fields):
        """
        Add the provided fields to this target's definition
        """
        merge_dicts(fields, self.data, RESERVED_KEYS_TARGET)
        if "display_name" in fields: # Exception to reserved key rule
            self.data["display_name"] = fields["display_name"]

    def bestow_fields(self, page):
        """
        Pass on inheritable fields from the target definition to the given page
        definition.
        """
        merge_dicts(self.data, page, RESERVED_KEYS_TARGET)

    def provide_page_title(page):
        """
        Return a suitable title for a page, if it doesn't have one.
        If the first two lines look like a Markdown header, use that.
        Otherwise, return the filename."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
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
        except FileNotFoundError as e:
            logger.warning("Couldn't guess title of page (file not found): %s" % e)

        #basically if the first line's not a markdown header, we give up and use
        # the filename instead
        return os.path.basename(filepath)

    def expand_openapi_spec(self, page):
        """Expand OpenAPI Spec placeholders into a full page list"""
        assert OPENAPI_SPEC_KEY in page.keys():

        logger.debug("Expanding OpenAPI spec from placeholder: %s"%page)
        api_slug = page.get(API_SLUG_KEY, None)
        extra_fields = {k:v for k,v in page.items()
                        if k not in [OPENAPI_SPEC_KEY, API_SLUG_KEY]}
        self.bestow_fields(extra_fields)
        template_path = page.get(OPENAPI_TEMPLATE_PATH_KEY, None)
        swagger = ApiDef.from_path(page[OPENAPI_SPEC_KEY], api_slug,
                                       extra_fields, template_path)
        return swagger.create_pagelist()

    def update_pages(self):
        """
        Find the set of pages that this target should include.  At this time,
        we expand OpenAPI spec placeholders into individual pages, read
        frontmatter, and so on. Save it to self.pages for later reference.
        """
        pages = []
        for page in self.config["pages"]:
            if not self.should_include(page):
                continue # Skip out-of-target pages

            # Expand OpenAPI Spec placeholders into full page lists
            if OPENAPI_SPEC_KEY in page.keys():
                try:
                    swagger_pages = self.expand_openapi_spec(page)
                    logger.debug("Adding generated OpenAPI reference pages: %s"%swagger_pages)
                    pages += swagger_pages
                except Exception as e:
                    self.error("Error when parsing OpenAPI definition %s" % page, e)
                    # Omit the API def from the page list if an error occurred

            # Normal in-target pages; provide some default values,
            # then add them to the list
            else:
                rawtext, frontmatter = parse_frontmatter(page)
                if "md" in page and "name" not in page:
                    #TODO: possibly load from frontmatter
                    logger.debug("Guessing page name for page %s" % page)
                    page_path = os.path.join(self.config["content_path"], page["md"])
                    page["name"] = guess_title_from_md_file(page_path)

                if "html" not in page:
                    page["html"] = self.html_filename_from(page)

                self.bestow_fields(page)
                pages.append(page)

        # Check for pages that would overwrite each other
        html_outs = set()
        for p in pages:
            if p["html"] in html_outs:
                self.error(("Repeated output filename '%s': "+
                    "the earlier instances will be overwritten") % p["html"])
            html_outs.add(p["html"])

        self.pages = pages

    def categories(self):
        """Produce an ordered, de-duplicated list of categories from
           this target's page list"""
        categories = []
        for page in self.pages:
            if "category" in page and page["category"] not in categories:
                categories.append(page["category"])
        logger.debug("categories: %s" % categories)
        return categories
