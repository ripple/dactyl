################################################################################
## OpenAPI Specification Parsing
##
## Parses an OpenAPI spec in YAML or JSON and generates files from it
################################################################################

import jinja2
import json
import requests
import datetime
from urllib.parse import unquote as urldecode
from copy import deepcopy
from ruamel.yaml.comments import CommentedMap as YamlMap
from ruamel.yaml.comments import CommentedSeq as YamlSeq

from dactyl.common import *
from dactyl.http_constants import HTTP_METHODS, HTTP_STATUS_CODES, HTTP_METHODS_WITH_REQ_BODIES

DATA_TYPES_SUFFIX = "-data-types"
METHOD_TOC_SUFFIX = "-methods"

TOC_TEMPLATE = "template-openapi_endpoint_toc.md"
TAG_TOC_TEMPLATE = "template-openapi_endpoint_tag_toc.md"
ENDPOINT_TEMPLATE = "template-openapi_endpoint.md"
DATA_TYPES_TOC_TEMPLATE = "template-openapi_data_types_toc.md"
DATA_TYPE_TEMPLATE = "template-openapi_data_type.md"

class ApiDef:
    cached_specs = {}
    def __init__(self, spec_path, api_slug=None, extra_fields={},
                template_path=None):
        self.read_swag(spec_path)
        self.clean_up_swag()
        self.deref_swag()

        try:
            self.api_title = self.swag["info"]["title"]
        except IndexError:
            self.api_title = fname.replace(".yml","")+" API (working title)"

        if api_slug is None:
            self.api_slug = slugify(self.api_title)
        else:
            self.api_slug = api_slug

        self.extra_fields = extra_fields
        self.setup_jinja_env(template_path)

    @classmethod
    def from_path(cls, spec_path, api_slug=None, extra_fields={},
                template_path=None):
        """
        Instantiate an ApiDef instance only if we haven't done so already. This
        saves the trouble of fetching & parsing API specs more than once.
        """
        if spec_path in cls.cached_specs.keys():
            return cls.cached_specs[spec_path]

        apidef = cls(spec_path, api_slug=api_slug,
                extra_fields=extra_fields, template_path=template_path)
        cls.cached_specs[spec_path] = apidef
        return apidef

    def read_swag(self, spec_path):
        """Read the OpenAPI definition from either a local file or a URL, and
        store it at self.swag"""
        logger.debug("Reading OpenAPI definition from %s"%spec_path)

        if spec_path[:5] == "http:" or spec_path[:6] == "https:":
            response = requests.get(spec_path)
            if response.status_code == 200:
                self.swag = yaml.load(response.text)
            else:
                raise requests.RequestException("Status code for page was not 200")
        else:
            with open(spec_path, "r", encoding="utf-8") as f:
                self.swag = yaml.load(f)


    def setup_jinja_env(self, template_path=None):
        """Sets up the environment used to inject OpenAPI data into Markdown
        templates"""
        if template_path is None:
            loader = jinja2.PackageLoader(__name__)
        else:
            logger.debug("OpenAPI spec: preferring templates from %s"%template_path)
            loader = jinja2.ChoiceLoader([
                jinja2.FileSystemLoader(template_path),
                jinja2.PackageLoader(__name__)
            ])
        self.env = jinja2.Environment(loader=loader, extensions=['jinja2.ext.i18n'])
        self.env.lstrip_blocks = True
        self.env.rstrip_blocks = True

    @staticmethod
    def dig(parts, context):
        """
        Search a context object for something matching a $ref (recursive)
        """
        key = parts[0].replace("~1", "/").replace("~0", "~") # unescaped
        key = urldecode(key)
        try:
            key = int(key)
        except:
            pass
        if key not in context.keys():
            raise IndexError(key)

        if len(parts) == 1:
            return context[key]
        else:
            return ApiDef.dig(parts[1:], context[key])

    def deref(self, ref):
        """Look through the YAML for a specific reference key, and return
        the value that key represents.
        - Raises IndexError if the key isn't found
            in the YAML.
        - add_title: If true, provide a "title" field when the reference
            resolves to an object that doesn't have a "title". The provided
            "title" value is based on the key that contained the reference
        """
        assert len(ref) > 1 and ref[0] == "#" and ref[1] == "/"
        parts = ref[2:].split("/")
        assert len(parts) > 0

        return self.dig(parts, self.swag)

    def deref_swag(self):
        """
        Walk the OpenAPI specification for $ref objects and resolve them to
        the values they reference. Assumes the entire spec is contained in a
        single file.
        """

        def deref_yaml(yaml_value):
            if "keys" in dir(yaml_value): # Dictionary-like type
                if "$ref" in yaml_value.keys():
                    # It's a reference; deref it
                    reffed_value = self.deref(yaml_value["$ref"])
                    # The referenced object may contain more references, so
                    # resolve those before returning
                    return deref_yaml(reffed_value)
                else:
                    # recurse through each key/value pair looking for refs
                    the_copy = YamlMap()
                    for k,v in yaml_value.items():
                        the_copy[k] = deref_yaml(v)
                    return the_copy
            elif "append" in dir(yaml_value): # List-like type
                # recurse through each item looking for refs
                the_copy = YamlSeq()
                for item in yaml_value:
                    the_copy.append(deref_yaml(item))
                return the_copy
            else: # Probably a basic type
                # base case: return the value
                return yaml_value

        self.swag = deref_yaml(self.swag)

    def clean_up_swag(self):
        # Give each schema in the "components" a title if it's missing one
        schemas = self.swag.get("components", {}).get("schemas", {})
        for key,schema in schemas.items():
            title = schema.get("title", key)
            schema["title"] = title
            if "example" in schema:
                try:
                    j = json.dumps(schema["example"], indent=4, default=self.json_default)
                    schema["example"] = j
                except Exception as e:
                    logger.debug("%s example isn't json: %s"%(title,j))
        self.deref_swag()

        # Find all tags used in endpoints and add any undefined ones to the
        # top level OpenAPI Object
        taglist = self.swag.get("tags", [])
        for path, method, endpoint in self.endpoint_iter():
            etags = endpoint.get("tags", [])
            for tag in etags:
                if tag not in [t.get("name") for t in taglist]:
                    taglist.append({
                        "name": tag,
                    })
        self.swag["tags"] = taglist


    def render_method_toc(self):
        t = self.env.get_template(TOC_TEMPLATE)
        context = self.new_context()
        context["endpoints"] = self.endpoint_iter()
        context["endpoints_by_tag"] = self.endpoint_iter
        return t.render(self.swag, **context)

    def render_tag_toc(self, tag):
        t = self.env.get_template(TAG_TOC_TEMPLATE)
        context = self.new_context()
        context["tag"] = tag
        context["endpoints"] = self.endpoint_iter()
        context["endpoints_by_tag"] = self.endpoint_iter
        return t.render(self.swag, **context)

    def render_data_types_toc(self):
        t = self.env.get_template(DATA_TYPES_TOC_TEMPLATE)
        context = self.new_context()
        context["schemas"] = self.data_type_iter()
        return t.render(self.swag, **context)

    def render_data_type(self, key, schema):
        t = self.env.get_template(DATA_TYPE_TEMPLATE)
        context = self.new_context()
        if "title" not in schema.keys():
            schema["title"] = key
        return t.render(schema, **context)

    def render_endpoint(self, path, method, endpoint):
        t = self.env.get_template(ENDPOINT_TEMPLATE)
        context = self.new_context()
        context["method"] = method
        context["path"] = path
        context["path_params"] = [p for p in endpoint.get("parameters",[]) if p["in"]=="path"]
        context["query_params"] = [p for p in endpoint.get("parameters",[]) if p["in"]=="query"]
        context["x_example_request_body"] = self.get_x_example_request_body(path,method,endpoint)
        #TODO: header & cookie params?? example response body?
        return t.render(endpoint, **context)

    def get_x_example_request_body(self, path, method, endpoint):
        if method not in HTTP_METHODS_WITH_REQ_BODIES:
            return ""

        content = endpoint.get("requestBody",{}).get("content",{})
        if not content:
            return ""
        for mediatype,content_inner in content.items():
            if "example" in content_inner:
                # single example
                ex = content_inner["example"]
            else:
                try:
                    # multiple examples? use the first one
                    ex = list(content_inner["examples"].values())[0]["value"]
                except (IndexError, KeyError, AttributeError) as e:
                    logger.debug("Media type %s didn't have an example value"%mediatype)
                    return ""

            try:
                ex_pp = json.dumps(ex, indent=4, separators=(',', ': '), default=self.json_default)
            except TypeError as e:
                traceback.print_tb(e.__traceback__)
                logger.debug("json dumps failed on example '%s'"%ex)
                ex_pp = ex
            return ex_pp

        logger.debug("couldn't find an example value for %s %s"%(method,path))
        return ""

    def get_endpoint_renderer(self, path, method, endpoint):
        return lambda: self.render_endpoint(path, method, endpoint)

    def get_data_type_renderer(self, key, schema):
        return lambda: self.render_data_type(key, schema)

    def get_tag_toc_renderer(self, tag):
        return lambda: self.render_tag_toc(tag)

    def endpoint_iter(self, tag=None):
        paths = self.swag.get("paths", {})
        for path, path_def in paths.items():
            for method in HTTP_METHODS:
                if method in path_def.keys():
                    endpoint = path_def[method]
                    if tag==None or tag in endpoint.get("tags", []) or \
                            (tag=="Uncategorized" and endpoint.get("tags", []) == []):
                        # TODO: Inherit parameters from the path definition itself
                        # Fill in some "sensible defaults" for fields we really want
                        operationId = endpoint.get("operationId", slugify(method+path))
                        endpoint["operationId"] = operationId
                        summary = endpoint.get("summary", operationId)
                        endpoint["summary"] = summary
                        yield (path, method, endpoint)

    def data_type_iter(self):
        schemas = self.swag.get("components", {}).get("schemas", {})
        for key,schema in schemas.items():
            title = schema.get("title", key)
            schema["title"] = title
            yield (title, schema)

    def create_pagelist(self):
        """
        Return an array of pages representing this API, which Dactyl can use
        as it would use a normal list of pages in the config
        """
        pages = []

        # TODO: make all the blurb/category strings template strings that can
        #       be translated and configured

        # add methods table of contents
        toc_page = deepcopy(self.extra_fields)
        toc_page.update({
            "name": "All "+self.api_title+" Methods",
            "__md_generator": self.render_method_toc,
            "html": self.api_slug+METHOD_TOC_SUFFIX+".html",
            "blurb": "List of methods/endpoints available in "+self.api_title,
            "category": "All "+self.api_title+" Methods",
        })
        if "parent" not in toc_page:
            toc_page["parent"] = "index.html"
        pages.append(toc_page)

        # add a table of contents per tag
        for tag in self.swag.get("tags",[{"name": "Uncategorized","description":""}]):
            tag_toc_page = deepcopy(self.extra_fields)
            tag_toc_page.update({
                "name": tag["name"].title()+" Methods",
                "__md_generator": self.get_tag_toc_renderer(tag),
                "html": self.api_slug+"-"+tag["name"]+METHOD_TOC_SUFFIX+".html",
                "blurb": tag.get("description",""),
                "category": tag["name"].title()+" Methods",
                "parent": toc_page["html"],
            })
            pages.append(tag_toc_page)

            # Add endpoints for this tag, except duplicates
            for path, method, endpoint in self.endpoint_iter(tag["name"]):
                tag0 = endpoint.get("tags",["Uncategorized"])[0]
                if tag0 != tag["name"]:
                    continue # Skip method whose primary tag is not this one
                method_page = deepcopy(self.extra_fields)
                method_page.update({
                    "name": endpoint["summary"],
                    "__md_generator": self.get_endpoint_renderer(path, method, endpoint),
                    "html": self.method_link(path, method, endpoint),
                    "blurb": endpoint.get("description", endpoint["operationId"]+" method"),
                    "category": tag0+" Methods",
                    "parent": tag_toc_page["html"],
                })
                pages.append(method_page)

        # add data types table of contents
        data_types_page = deepcopy(self.extra_fields)
        data_types_page.update({
            "name": self.api_title+" Data Types",
            "__md_generator": self.render_data_types_toc,
            "html": self.api_slug+DATA_TYPES_SUFFIX+".html",
            "blurb": "List of all data types defined for "+self.api_title,
            "category": self.api_title+" Data Types",
            "parent": toc_page["html"],
        })
        pages.append(data_types_page)

        # add each data type from the components.schemas list
        schemas = self.swag.get("components", {}).get("schemas", {})
        for title, schema in self.data_type_iter():
            data_type_page = deepcopy(self.extra_fields)
            data_type_page.update({
                "name": title,
                "__md_generator": self.get_data_type_renderer(title, schema),
                "html": self.type_link(title),
                "blurb": "Definition of "+title+" data type",
                "category": self.api_title+" Data Types",
                "parent": data_types_page["html"],
            })
            pages.append(data_type_page)

        return pages

    def add_metadata(self, target_data):
        """
        Extend the provided target_data dictionary with metadata pulled from
        the spec.
        """
        info = self.swag.get("info", {"title":self.api_title, "version":"0.0.0"})
        target_data["info"] = info


    def new_context(self):
        return {
            "api_title": self.api_title,
            "type_link": self.type_link,
            "method_link": self.method_link,
            "HTTP_METHODS": HTTP_METHODS,
            "HTTP_STATUS_CODES": HTTP_STATUS_CODES,
            "spec": self.swag,
            "debug": logger.debug,
            "slugify": slugify,
            "md_escape": self.md_escape,
        }

    @staticmethod
    def md_escape(text):
        """
        Escape potential Markdown syntax in a string.
        This is meant to be passed to the templates.
        """
        specialchars = "\\`*_{}[]()#+-.!"
        s = ""
        for c in text:
            if c in specialchars:
                s += "\\"
            s += c
        return s

    @staticmethod
    def json_default(o):
        """
        Serializer function for JSON (from YAML)
        """
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        else:
            return str(o)

    def type_link(self, title):
        # TODO: in "md" mode, use ".md" suffix
        return self.api_slug+DATA_TYPES_SUFFIX+"-"+slugify(title.lower())+".html"

    def method_link(self, path, method, endpoint):
        return self.api_slug+"-"+slugify(endpoint["operationId"]+".html")
