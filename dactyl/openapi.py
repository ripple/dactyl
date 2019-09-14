################################################################################
## OpenAPI Specification Parsing
##
## Parses an OpenAPI spec in YAML or JSON and generates files from it
################################################################################

import jinja2
from copy import deepcopy

from dactyl.common import *

DATA_TYPES_SUFFIX = "-data-types"
METHOD_TOC_SUFFIX = "-methods"
HTTP_METHODS = [
    "get",
    "put",
    "post",
    "delete",
    "options",
    "head",
    "patch",
    "trace",
]
TOC_TEMPLATE = "template-openapi_endpoint_toc.md"
ENDPOINT_TEMPLATE = "template-openapi_endpoint.md"
DATA_TYPES_TEMPLATE = "template-openapi_data_types.md"

class ApiDef:
    def __init__(self, fname, api_slug=None, extra_fields={},
                template_path=None):
        with open(fname, "r", encoding="utf-8") as f:
            self.swag = yaml.load(f)

        try:
            self.api_title = self.swag["info"]["title"]
        except IndexError:
            self.api_title = fname.replace(".yml","")+" API (working title)"

        if api_slug is None:
            self.api_slug = slugify(self.api_title)
        else:
            self.api_slug = api_slug

        self.extra_fields = extra_fields

        if template_path is None:
            loader = jinja2.PackageLoader(__name__)
        else:
            loader = jinja2.ChoiceLoader(
                jinja2.FileSystemLoader(template_path),
                jinja2.PackageLoader(__name__)
            )
        self.env = jinja2.Environment(loader=loader)

    def deref(self, ref, add_title=False):
        assert len(ref) > 1 and ref[0] == "#" and ref[1] == "/"
        parts = ref[2:].split("/")
        assert len(parts) > 0

        def dig(parts, context):
            key = parts[0].replace("~1", "/").replace("~0", "~") # unescaped
            try:
                key = int(key)
            except:
                pass
            if key not in context.keys():
                raise IndexError(key)

            if len(parts) == 1:
                if add_title:
                    context[key]["title"] = parts[0]
                return context[key]
            else:
                return dig(parts[1:], context[key])

        return dig(parts, self.swag)

    # def render(self):
    #     self.write_file(self.render_toc(), self.api_slug+METHOD_TOC_SUFFIX+".md")
    #
    #     for path, path_def in self.swag["paths"].items():
    #         #TODO: inherit path-generic fields
    #         for method in HTTP_METHODS:
    #             if method in path_def.keys():
    #                 endpoint = path_def[method]
    #                 to_file = self.method_file(path, method, endpoint)
    #                 self.write_file(self.render_endpoint(path, method, endpoint), to_file)
    #
    #     self.write_file(self.render_data_types(), self.api_slug+DATA_TYPES_SUFFIX+".md")

    def render_toc(self):
        t = self.env.get_template(TOC_TEMPLATE)
        context = self.new_context()
        return t.render(self.swag, **context)

    def render_data_types(self):
        t = self.env.get_template(DATA_TYPES_TEMPLATE)
        context = self.new_context()
        schemas = self.swag["components"]["schemas"]

        # Dereference properties first
        for cname, c in schemas.items():
            if "properties" in c.keys():
                for pname, p in c["properties"].items():
                    if "$ref" in p.keys():
                        schemas[cname]["properties"][pname] = self.deref(p["$ref"])

        # Dereference aliased data types
        for cname, c in schemas.items():
            if "$ref" in c.keys():
                schemas[cname] = self.deref(c["$ref"])

        return t.render(**context, schemas=schemas)

    def get_endpoint_renderer(self, path, method, endpoint):
        return lambda: self.render_endpoint(path, method, endpoint)

    def render_endpoint(self, path, method, endpoint):
        t = self.env.get_template(ENDPOINT_TEMPLATE)
        context = self.new_context()
        context["method"] = method
        context["path"] = path
        context["path_params"] = [p for p in endpoint.get("parameters",[]) if p["in"]=="path"]
        for p in context["path_params"]:
            if "schema" in p.keys() and "$ref" in p["schema"].keys():
                p["schema"] = self.deref(p["schema"]["$ref"], add_title=True)
                # add_title is a hack since the XRP-API ref doesn't use titles
        context["query_params"] = [p for p in endpoint.get("parameters",[]) if p["in"]=="query"]
        for p in context["path_params"]:
            if "schema" in p.keys() and "$ref" in p["schema"].keys():
                p["schema"] = self.deref(p["schema"]["$ref"], add_title=True)
        #TODO: header & cookie params??
        return t.render(endpoint, **context)

    def create_pagelist(self):
        pages = []

        # TODO: make all the blurb/category strings template strings that can
        #       be translated and configured

        # add data types page
        data_types_page = deepcopy(self.extra_fields)
        data_types_page.update({
            "name": self.api_title+" Data Types",
            "__md_generator": self.render_data_types,
            "html": self.api_slug+DATA_TYPES_SUFFIX+".html",
            "blurb": "Definitions for all data types in "+self.api_title,
            "category": self.api_title+" Conventions",
        })
        pages.append(data_types_page)

        # add methods table of contents
        toc_page = deepcopy(self.extra_fields)
        toc_page.update({
            "name": self.api_title+" Methods",
            "__md_generator": self.render_toc,
            "html": self.api_slug+METHOD_TOC_SUFFIX+".html",
            "blurb": "List of methods/endpoints available in "+self.api_title,
            "category": self.api_title+" Methods",
        })
        pages.append(toc_page)

        # add each endpoint
        for path, path_def in self.swag["paths"].items():
            for method in HTTP_METHODS:
                if method in path_def.keys():
                    endpoint = path_def[method]

                    method_page = deepcopy(self.extra_fields)
                    method_page.update({
                        "name": endpoint["operationId"],
                        "__md_generator": self.get_endpoint_renderer(path, method, endpoint),
                        "html": self.method_link(path, method, endpoint),
                        "blurb": endpoint.get("description", endpoint["operationId"]+" method"),
                        "category": self.api_title+" Methods",
                    })
                    pages.append(method_page)

        # yaml2 = ruamel.yaml.YAML()
        # yaml2.indent(offset=4, sequence=8)
        # out_path = os.path.join(OUT_DIR, YAML_OUT_FILE)
        # with open(out_path, "w", encoding="utf-8") as f:
        #     yaml2.dump({"pages":pages}, f)
        return pages

    def new_context(self):
        return {
            "api_title": self.api_title,
            "type_link": self.type_link,
            "method_link": self.method_link,
            "HTTP_METHODS": HTTP_METHODS,
        }

    # def write_file(self, page_text, filepath):
    #     out_folder = os.path.join(self.out_dir, os.path.dirname(filepath))
    #     if not os.path.isdir(out_folder):
    #         os.makedirs(out_folder)
    #     fileout = os.path.join(out_folder, filepath)
    #     with open(fileout, "w", encoding="utf-8") as f:
    #         f.write(page_text)


    def type_link(self, title):
        return self.api_slug+DATA_TYPES_SUFFIX+".html#"+slugify(title.lower())

    def method_link(self, path, method, endpoint):
        return self.api_slug+"-"+slugify(endpoint["operationId"]+".html")
