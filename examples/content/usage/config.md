---
parent: usage.html
targets:
  - everything
---
# Configuration

Dactyl is intended to be used with a config file containing a list of pages to parse. Pages are grouped into "targets" that represent a group of documents to be built together; a page can belong to multiple targets, and can even contain conditional syntax so that it builds differently depending on the target in question. Targets and pages can also use different templates from each other, and pages can inherit semi-arbitrary key/value pairs from the targets.

The input pages in the config file should be specified relative to the `content_path`, which is `content/` by default. You can also specify a URL to pull in a Markdown file from a remote source, but if you do, Dactyl won't run any pre-processing on it.

## Directory Paths
An advanced setup would probably have a directory structure such as the following:

```
./                      # Top-level dir; this is where you run dactyl_*
./dactyl-config.yml     # Default config file name
./content               # Dir containing your .md source files
---------/*/*.md        # You can sort .md files into subdirs if you like
---------/static/*      # Static images referencd in your .md files
./templates/template-*.html # Custom HTML Templates
./assets                # Directory for static files referenced by templates
./out                   # Directory where output gets generated. Can be deleted
```

All of these paths can be configured.

## Targets

A target represents a group of pages, which can be built together or concatenated into a single PDF. You should have at least one target defined in the `targets` array of your Dactyl config file. A target definition should consist of a short `name` (used to specify the target in the commandline and elsewhere in the config file) and a human-readable `display_name` (used mostly by templates but also when listing targets on the commandline).

A simple target definition:

```yaml
targets:
    -   name: kc-rt-faq
        display_name: Ripple Trade Migration FAQ
```

In addition to `name` and `display_name`, a target definition can contain arbitrary key-values to be inherited by all pages in this target. Dictionary values are inherited such that keys that aren't set in the page are carried over from the target, recursively. The rest of the time, fields that appear in a page definition take precedence over fields that appear in a target definition.

Some things you may want to set at the target level include `filters` (an array of filters to apply to pages in this target), `template` (template to use when building HTML), and `pdf_template` (template to use when building PDF). You can also use the custom values in templates and preprocessing. Some filters define additional fields that affect the filter's behavior.

The following field names cannot be inherited: `name`, `display_name`, and `pages`.

## Pages

Each page represents one HTML file in your output. A page can belong to one or more targets. When building a target, all the pages belonging to that target are built in the order they appear in the `pages` array of your Dactyl config file.

Example of a pages definition with two files:

```yaml
pages:
    -   name: RippleAPI
        category: References
        html: reference-rippleapi.html
        md: https://raw.githubusercontent.com/ripple/ripple-lib/0.17.2/docs/index.md
        filters:
            - remove_doctoc
            - add_version
        targets:
            - local
            - ripple.com

    -   name: rippled
        category: References
        html: reference-rippled.html
        md: reference-rippled.md
        targets:
            - local
            - ripple.com
```

Each individual page definition can have the following fields:

| Field                    | Type      | Description                           |
|:-------------------------|:----------|:--------------------------------------|
| `targets`                | Array     | The short names of the targets that should include this page. |
| `html`                   | String    | _(Optional)_ The filename where this file should be written in the output directory. If omitted, Dactyl chooses a filename based on the `md` field (if provided), the `name` field (if provided), or the current time (as a last resort). By default, generated filenames flatten the folder structure of the md files. To instead replicate the folder structure of the source documents in auto-generated filenames, add `flatten_default_html_paths: true` to the top level of your Dactyl config file. |
| `name`                   | String    | _(Optional)_ Human-readable display name for this page. If omitted but `md` is provided, Dactyl tries to guess the right file name by looking at the first two lines of the `md` source file. |
| `md`                     | String    | _(Optional)_ The markdown filename to parse to generate this page, relative to the **content_path** in your config. If this is not provided, the source file is assumed to be empty. (You might do that if you use a nonstandard `template` for this page.) |
| `openapi_specification`  | String    | _(Optional)_ The file path or http(s) URL to an OpenAPI v3.0 specification to be parsed into generated documentation. If provided, this entry becomes expanded into a set of several pages that describe the methods and data types defined for the given API. The generated pages inherit the other fields of this page object. **Experimental.** If the path is a relative path, it is evaluated based on the directory Dactyl is called from, not the content directory. |
| `api_slug`               | String    | _(Optional)_ If this is an `openapi_specification` entry,
| `category` | String | _(Optional)_ The name of a category to group this page into. This is used by Dactyl's built-in templates to organize the table of contents. |
| `template`               | String    | _(Optional)_ The filename of a custom [Jinja][] HTML template to use when building this page for HTML, relative to the **template_path** in your config. |
| `pdf_template`           | String    | _(Optional)_ The filename of a custom [Jinja][] HTML template to use when building this page for PDF, relative to the **template_path** in your config. |
| `openapi_md_template_path` | String | _(Optional)_ Path to a folder containing [templates to be used for OpenAPI spec parsing](openapi.html). If omitted, use the [built-in templates](templates.html). |
| `parent`                 | String    | _(Optional)_ The HTML filename of the page to treat as a parent of this one for purposes of hierarchy. If omitted, treat the page as a "top-level" page. |
| ...                      | (Various) | Additional arbitrary key-value pairs as desired. These values can be used by templates or pre-processing. |

If the file specified by `md` begins with YAML frontmatter, separated by a line of exactly `---`, the frontmatter is used as a basis for these fields. Certain frontmatter fields are adapted from Jekyll format to Dactyl format: for example, `title` gets copied to `name` if the page does not have a `name`.

The following fields are automatically added after a page has been parsed to HTML. (They're not available when preprocessing or rendering Markdown to HTML, but _are_ available when rendering HTML templates.)

| Field                    | Type      | Description                           |
|:-------------------------|:----------|:--------------------------------------|
| `plaintext` | String     | A plaintext-only version of the page's markdown content, with all Markdown and HTML syntax removed. |
| `headermap` | Dictionary | A mapping of the page's headers to the unique IDs of those headers in the generated HTML version. |
| `blurb`     | String     | An introductory blurb generated from the page's first paragraph of text. |
| `children`  | List       | A list of pages, in order of appearance, that refer to this page as their `parent`. Each of these "child" pages is a reference to the page definition (dictionary) for that child. |
| `is_ancestor_of` | Function | A function that takes one argument, the string identifying a potential child page by that child's `html` field. This function returns `True` if this page is a direct or indirect parent of the child page. |

[Jinja]: http://jinja.pocoo.org/
