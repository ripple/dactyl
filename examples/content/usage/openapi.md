---
parent: usage.html
targets: [everything]
---
# OpenAPI Specifications

Dactyl can parse an [OpenAPI v3.0 specification](https://github.com/OAI/OpenAPI-Specification) to generate API documentation for the API that specification describes, including API methods and object schemas.

## Ad-Hoc Usage

You can use the `--openapi <specfile>` parameter to build a single target from

```sh
dactyl_build --openapi openapi.yaml
```

You can combine this with `--md` or `--pdf` to output the generated documentation in Markdown or PDF format, respectively.


## Config File
You can add a special entry to the `pages` array to represent an API reference; Dactyl will expand that file into multiple pages that each inherit any fields of this entry. For example:

```
-   openapi_specification: https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/petstore.yaml
    api_slug: petstore
    foo: bar
    targets:
        - baz
```

The `api_slug` field is optional, and provides a prefix that gets used for a bunch of file names and stuff. You can use the other fields to specify which HTML templates to use or to pass more info to those templates to control how they display.

The generated pages are:

- An "All Methods" table of contents, listing every path operation in the `paths` of the OpenAPI specification.
- "Tag Methods" table of contents pages for each `tag` used in the OpenAPI specification.
- Pages for all "API Methods" (path operations) in `paths` of the OpenAPI specification.
- A "Data Types" table of contents, listing every data type defined in the `schema` section of the OpenAPI specification.
- Individual pages for each data type in the OpenAPI specification's `schema` section.

## Custom Templates

You can override the [templates used for generated OpenAPI pages](#openapi-spec-templates) to adjust how the Markdown is generated.

In the page or target definition of your config file, set the `openapi_md_template_path` field to a path that contains the following templates:

| Filename                               | Template for...                     |
|:---------------------------------------|:------------------------------------|
| `template-openapi_data_type.md`        | Each individual data type in the spec's `schema` section. |
| `template-openapi_data_types_toc.md`   | Table of contents for the data types. |
| `template-openapi_endpoint_tag_toc.md` | Table of contents for each endpoint `tag` in the spec. |
| `template-openapi_endpoint_toc.md`     | Table of contents for all endpoints and tags. |
| `template-openapi_endpoint.md`         | Table of contents for each individual endpoint in the `paths` section. |

These templates use [Jinja](http://jinja.pocoo.org/) syntax.
