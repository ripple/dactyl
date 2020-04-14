# Dactyl

Documentation tools for enterprise-quality documentation from Markdown source. Dactyl has advanced features to enable [single-sourcing](https://en.wikipedia.org/wiki/Single_source_publishing) and an extensible syntax for building well-organized, visually attractive docs. It generates output in HTML (natively), and can make PDFs if you have [Prince][] installed.

[Prince]: http://www.princexml.com/

## Installation

Dactyl requires [Python 3](https://python.org/). Install with [pip](https://pip.pypa.io/en/stable/):

```
sudo pip3 install dactyl
```

Or a local install in a virtualenv:

```sh
# Create an activate a virtualenv so the package and dependencies are localized
virtualenv -p `which python3` venv_dactyl
source venv_dactyl/bin/activate

# Check out this repo
git clone https://github.com/ripple/dactyl

# Install
pip3 install dactyl/

# Where 'dactyl/' is the top level directory of the repo, containing setup.py.
# And note the trailing '/' which tells pip to use a local directory to install it.
```

## Usage

Simple ("Ad-Hoc") usage:

```sh
$ dactyl_build --pages input1.md input2.md
```

By default, the resulting HTML pages are written to a folder called `out/` in the current working directory. You can specify a different output path in the config file or by using the `-o` parameter.

### Building PDF

Dactyl generates PDFs by making temporary HTML files and running [Prince][]. Use the `--pdf` command to generate a PDF. Dactyl tries to come up with a sensible output filename by default, or you can provide one (which must end in `.pdf`):

```sh
$ dactyl_build --pages input1.md input2.md --pdf MyGuide.pdf
```

### Advanced Usage

Dactyl is intended to be used with a config file containing a list of pages to parse. Pages are grouped into "targets" that represent a group of documents to be built together; a page can belong to multiple targets, and can even contain conditional syntax so that it builds slightly different depending on the target in question. Targets and pages can also use different templates from each other, and pages can inherit semi-arbitrary key/value pairs from the targets.

For more information on configuration, see the `default-config.yml` and the [examples](examples/) folder.

The input pages in the config file should be specified relative to the `content_path`, which is `content/` by default. You can also specify a URL to pull in a markdown file from a remote source, but if you do, Dactyl won't run any pre-processing on it.

For a full list of Dactyl options, use the `-h` parameter.

#### Specifying a Config File

By default, Dactyl looks for a config file named `dactyl-config.yml` in the current working directory. You can specify an alternate config file with the `-c` or `--config` parameter:

```sh
$ dactyl_build -c path/to/alt-config.yml
```

For more information on configuration, see the `default-config.yml` and the [examples](examples/) folder.

#### Specifying a Target

If your config file contains more than one **target**, Dactyl builds the first one by default. You can specify a different target by passing its `name` value with the `-t` parameter:

```sh
$ dactyl_build -t non-default-target
```

#### Static Files

Your templates may require certain static files (such as JavaScript, CSS, and images) to display properly. Your content may have its own static files (such as diagrams and figures). By default, Dactyl assumes that templates have static files in the `assets/` folder. You can configure this path and also specify one or more paths to static files referenced by your content. When you build, Dactyl copies files from these folders to the output folder by default depending on which mode you're building:

| Build Mode         | Files copied to output folder by default                |
|:-------------------|:--------------------------------------------------------|
| HTML               | Both template and content static files                  |
| PDF                | Neither template nor content static files (cannot be overridden) |
| Markdown           | Content static files only                               |
| ElasticSearch JSON | Neither template nor content static files               |

You can use a commandline flag to explicitly specify what gets copied to the output folder, except in the case of PDF. (In PDF mode, Dactyl writes only the final PDF to the output folder.) The flags are as follows:

| Flag (long version) | Short version | Meaning                                |
|:--------------------|:--------------|:---------------------------------------|
| `--copy_static`     | `-s`          | Copy all static files to the out dir.  |
| `--no_static`       | `-S`          | Don't copy any static files to the out dir. |
| `--template_static` | `-T`          | Copy only templates' static files to the out dir |
| `--content_static`  | `-C`          | Copy only the content's static files to the out dir |

The following config file parameters control what paths Dactyl checks for static content:

| Field | Default | Description |
|---|---|---|
| `template_static_path` | `assets/` | Static files belonging to the templates. |
| `content_static_path` | (None) | Static files belonging to content. This can be a single folder path, as a string, or an array of paths to files or folders. Dactyl copies all files and folders (regardless of whether the current target uses them). |

#### Listing Available Targets

If you have a lot of targets, it can be hard to remember what the short names for each are. If you provide the `-l` flag, Dactyl will list available targets and then quit without doing anything:

```sh
$ dactyl_build -l
tests        Dactyl Test Suite
rc-install        Ripple Connect v2.6.3 Installation Guide
rc-release-notes        
kc-rt-faq        Ripple Trade Migration FAQ
```

#### Building Markdown

This mode runs the pre-processor only, so you can generate Markdown files that are more likely to display properly in conventional Markdown parsers (like the one built into GitHub). Use the `--md` flag to output Markdown files, skipping the HTML/PDF templates entirely.

```sh
$ dactyl_build --md
```

#### Building Only One Page

If you only want to build a single page, you can use the `--only` flag, followed by the filename you want to build (either the input filename ending in `.md` or the output filename ending in `.html`):

```sh
dactyl_build --only index.html --pdf
```

This command can be combined with the `--pdf` or `--md` flags. You can also use it with the `--target` setting (in case you want the context from the target even though you're only building one page.)

#### Watch Mode

You can use the `-w` flag to make Dactyl run continuously, watching for changes to its input templates or markdown files. Whenever it detects that a file has changed, Dactyl automatically rebuilds the output in whatever the current mode is, (HTML, PDF, or Markdown).

To be detected as a change, the file has to match one of the following patterns:

```
*.md
*/code_samples/*
template-*.html
```

Beware: some configurations can lead to an infinite loop. (For example, if your output directory is a subdirectory of your content directory and you use Dactyl in `--md` mode.)

**Limitations:** Watch mode can be combined with `--only`, but re-builds the page even when it detects changes to unrelated pages. Watch mode doesn't detect changes to the config file, static files, or filters.

To stop watching, interrupt the Dactyl process (Ctrl-C in most terminals).

#### ElasticSearch Compatibility

Dactyl has the ability to build JSON formatted for upload to [ElasticSearch](https://www.elastic.co/products/elasticsearch) and even upload it directly.

To build JSON files for upload to ElasticSearch, use the `--es` mode:

```
dactyl_build --es
```

This writes files to the usual output directory using an ElasticSearch JSON template. Dactyl skips any files that do not have a `md` source parameter in this mode. The output filenames are the pages' `html` filenames, except ending in `.json` instead of `.html`. You can specify a custom template for these JSON files using the top-level `default_es_template` field in the config file. This template must be a valid JSON file and has several special properties as described in [ElasticSearch JSON Templates](#elasticsearch-json-templates).

Dactyl can also upload these files directly to an ElasticSearch instance, even when building for another mode. For example, to build the HTML version of a target named `filterdemos` but also upload that target's JSON-formatted data to an ElasticSearch instance:

```
dactyl_build -t filterdemos --html --es_upload https://my-es-instance.example.com:9200
```

The parameter to `--es_upload` should be the base URL of your ElasticSearch index. You can omit the parameter to use the default base URL of `http://localhost:9200`.


#### ElasticSearch JSON Templates

Dactyl has a special format for JSON templates meant for creating ElasticSearch data. These templates must be valid JSON and are processed according to the following rules:

- Any strings in the fields' values are "preprocessed" in a similar context to the Jinja2-based Markdown preprocessor. For example, the string `{{currentpage.name}}` evaluates to the page's name.
- Any object containing the key `__dactyl_eval__` is evaluated as a Python expression. The object is replaced with the results of the expression, with lists becoming JSON arrays and dictionaries becoming JSON objects.
- The above rules apply recursively to values nested in arrays and objects. All other values are preserved literally.

The context provided to the preprocessing and to the `__dactyl_eval__` expressions is the same and contains the following:

| Field           | Python Type | Description                                  |
|:----------------|:------------|:---------------------------------------------|
| `currentpage`   | `dict`      | The current page definition (usually derived from the config file) |
| `target`        | `dict`      | The current target definition (usually derived from the config file) |
| `categories`    | `list`      | A list of unique `category` values used by pages in the current target, in order of appearance. |
| `page_filters`  | `list`      | A list of the names of Dactyl filters applied to the current page. |
| `mode`          | `str`       | Always equal to `es` in this context         |
| `current_time`  | `str`       | The current time, in the `time_format` specified in the config. (Defaults to YYYY-MM-DD) |
| `bypass_errors` | `bool`      | If `true`, this build is running with the option to continue through errors where possible. |


### OpenAPI Specification Parsing

Dactyl contains experimental support for automatically generating documentation from an [OpenAPI Specification](https://github.com/OAI/OpenAPI-Specification). Dactyl has partial support for **v3.0.x** of the OpenAPI spec.

From the commandline, you can generate documentation for a spec using the `--openapi` option, providing a file path or URL to the spec. For example:

```
dactyl_build --openapi https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/petstore.yaml
```

You can also [add an OpenAPI specification to a config file](#openapi-specifications), where the generated documentation can be part of a larger target that includes other files.



### Link Checking

The link checker is a separate script. It assumes that you've already built some documentation to an output path. Use it as follows:

```sh
$ dactyl_link_checker
```

This checks all the files in the output directory for links and confirms that any HTTP(S) links, including relative links to other files, are valid. For anchor links, it checks that an element with the correct ID exists in the target file. It also checks that the `src` of all image tags exists.

If there are links that are always reported as broken but you don't want to remove (for example, URLs that block Python's user-agent) you can add them to the `known_broken_links` array in the config.

In quiet mode (`-q`), the link checker still reports in every 30 seconds just so that it doesn't get treated as stalled and killed by continuous integration software (e.g. Jenkins).

To reduce the number of meaningless failure reports (because a particular website happened to be down momentarily while you ran the link checker), if there are any broken remote links, the link checker waits 2 minutes after finishing and then retries those links in case they came back up. (If they did, they're not considered broken for the link checker's final report.)

You can also run the link checker in offline mode (`-o`) to skip any remote links and just check that the files and anchors referenced exist in the output directory.

If you have a page that uses JavaScript or something to generate anchors dynamically, the link checker can't find those anchors (since it doesn't run any JS). You can add such pages to the `ignore_anchors_in` array in your config to skip checking for links that go to anchors in such pages.


### Style Checking

The style checker is experimental. It reads lists of discouraged words and phrases from the `word_substitutions_file` and `phrase_substitutions_file` paths (respectively) in the config. For each such word or phrase that appears in the output HTML (excluding `code`, `pre`, and `tt` elements), it counts and prints a violation, suggesting a replacement based on the word/phrase file.

The style checker re-generates HTML in-memory (never writing it out). It uses the first target in the config file unless you specify another target with `-t`.

Example usage:

```sh
$ dactyl_style_checker -t rippledevportal
Style Checker - checking all pages in target rippledevportal
Found 6 issues:
Page: Gateway Guide
   Discouraged phrase: in order to (1 instances); suggest 'to' instead.
   Discouraged phrase: and/or (1 instances); suggest '__ or __ or both' instead.
   Discouraged word: feasible (1 instances); suggest 'can be done, workable' instead.
   Discouraged phrase: in an effort to (1 instances); suggest 'to' instead.
   Discouraged phrase: comply with (1 instances); suggest 'follow' instead.
Page: Amendments
   Discouraged phrase: limited number (1 instances); suggest 'limits' instead.
```

You can add an exemption to a specific style rule with an HTML comment. The exemption applies to the whole output (HTML) file in which it appears.

```html
Maybe the word "will" is a discouraged word, but you really want to use it here without flagging it as a violation? Adding a comment like this <!-- STYLE_OVERRIDE: will --> makes it so.
```

## Configuration

Many parts of Dactyl are configurable. An advanced setup would probably have the following folders in your directory structure:

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

(All of these paths can be configured.)

### Targets

A target represents a group of pages, which can be built together or concatenated into a single PDF. You should have at least one target defined in the `targets` array of your Dactyl config file. A target definition should consist of a short `name` (used to specify the target in the commandline and elsewhere in the config file) and a human-readable `display_name` (used mostly by templates but also when listing targets on the commandline).

A simple target definition:

```
targets:
    -   name: kc-rt-faq
        display_name: Ripple Trade Migration FAQ
```

In addition to `name` and `display_name`, a target definition can contain arbitrary key-values to be inherited by all pages in this target. Dictionary values are inherited such that keys that aren't set in the page are carried over from the target, recursively. The rest of the time, fields that appear in a page definition take precedence over fields that appear in a target definition.

Some things you may want to set at the target level include `filters` (an array of filters to apply to pages in this target), `template` (template to use when building HTML), and `pdf_template` (template to use when building PDF). You can also use the custom values in templates and preprocessing. Some filters define additional fields that affect the filter's behavior.

The following field names cannot be inherited: `name`, `display_name`, and `pages`.

### Pages

Each page represents one HTML file in your output. A page can belong to one or more targets. When building a target, all the pages belonging to that target are built in the order they appear in the `pages` array of your Dactyl config file.

Example of a pages definition with two files:

```
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
| `openapi_md_template_path` | String | _(Optional)_ Path to a folder containing [templates to be used for OpenAPI spec parsing](#openapi-spec-templates). If omitted, use the [built-in templates](dactyl/templates/). |
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

[Jinja]: http://jinja.pocoo.org/

#### OpenAPI Specifications

You can add a special entry to the `pages` array to represent an OpenAPI v3.0 specification, which will be expanded into several pages representing the methods and data types specified in the file. For example:

```
-   openapi_specification: https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/petstore.yaml
    api_slug: petstore
    foo: bar
    targets:
        - baz
```

The `api_slug` field is optional, and provides a prefix that gets used for a bunch of file names and stuff. Other fields are inherited by all of the pages the specification builds, which are:

- An "All Methods" table of contents, listing every path operation in the `paths` of the OpenAPI specification.
- "Tag Methods" table of contents pages for each `tag` used in the OpenAPI specification.
- Pages for all "API Methods" (path operations) in `paths` of the OpenAPI specification.
- A "Data Types" table of contents, listing every data type defined in the `schema` section of the OpenAPI specification.
- Individual pages for each data type in the OpenAPI specification's `schema` section.

You can override the [templates used for generated OpenAPI pages](#openapi-spec-templates) to adjust how the Markdown is generated by providing the path to a different set of templates in the `openapi_md_template_path` field.


## Editing

Dactyl supports extended Markdown syntax with the [Python-Markdown Extra](https://pythonhosted.org/Markdown/extensions/extra.html) module. This correctly parses most GitHub-Flavored Markdown syntax (such as tables and fenced code blocks) as well as a few other features.

### Pre-processing

Dactyl pre-processes Markdown files by treating them as [Jinja][] Templates, so you can use [Jinja's templating syntax](http://jinja.pocoo.org/docs/dev/templates/) to do advanced stuff like include other files or pull in variables from the config or commandline. Dactyl passes the following fields to Markdown files when it pre-processes them:

| Field             | Value                                                    |
|:------------------|:---------------------------------------------------------|
| `target`          | The [target](#targets) definition of the current target. |
| `pages`           | The [array of page definitions](#pages) in the current target. Use this to generate navigation across pages. (The default templates don't do this, but you should.) |
| `currentpage`     | The definition of the page currently being rendered.     |
| `categories`      | A de-duplicated array of categories that are used by at least one page in this target, sorted in the order they first appear. |
| `config`          | The global Dactyl config object. |
| `content`         | The parsed HTML content of the page currently being rendered. |
| `current_time`    | The current date as of rendering. The format is YYYY-MM-DD by default; you can also set the `time_format` field to a custom [stftime format string](http://strftime.org/). |
| `mode`            | The output format: either `html` (default), `pdf`, or `md`. |


### Adding Variables from the Commandline

You can pass in a JSON or YAML-formatted list of variables using `--vars` commandline switch. Any such variables get added as fields of `target` and inherited by `currentpage` in any case where `currentpage` does not already have the same variable name set. For example:

```sh
$ cat md/vartest.md
Myvar is: '{{ target.myvar }}'

$ dactyl_build --vars '{"myvar":"foo"}'
rendering pages...
writing to file: out/index.html...
Preparing page vartest.md
reading markdown from file: vartest.md
... parsing markdown...
... modifying links for target: default
... re-rendering HTML from soup...
writing to file: out/test_vars.html...
done rendering
copying static pages...

$ cat out/test_vars.html | grep Myvar
<p>Myvar is: 'foo'</p></main>
```

If argument to `--vars` ends in `.yaml` or `.json`, Dactyl treats the argument as a filename and opens it as a YAML file. (YAML is a superset of JSON, so this works for JSON files.) Otherwise, Dactyl treats the argument as a YAML/JSON object directly. Be sure that the argument is quoted and escaped as necessary based on the commandline shell you use.

You cannot set the following reserved keys:

- `name`
- `display_name` (Instead, use the `--title` argument to set the display name of the target on the commandline.)
- `pages`


### Filters

Furthermore, Dactyl supports additional custom post-processing through the use of filters. Filters can operate on the markdown (after it's been pre-processed), on the raw HTML (after it's been parsed), or on a BeautifulSoup object representing the output HTML. Filters can also export functions and values that are available to the preprocessor.

Dactyl comes with several filters, which you can enable in your config file. You can also write your own filters. If you do, you must specify the paths to the folder(s) containing your filter files in the `filter_paths` array of the config file.

To enable a filter for a target or page, set the `filters` field of the config to be an array of filter names, where the filter names are derived from the Python source files in the format `filter_<filtername>.py`. Filter names must be valid Python variable names, so they can't start with a numeral and must contain only alphanumeric and underscore characters.

Dactyl automatically runs the following functions from filter files (skipping any that aren't defined):

1. Before running the preprocessor on a page, Dactyl adds all items from each filter's `export` global dictionary to the preprocessor environment.
2. Dactyl runs the `filter_markdown(md, **kwargs)` function of each filter after the preprocessor. This function receives the preprocessed markdown as a string in the `md` argument and must return a string with the markdown as filtered.
3. Dactyl runs the `filter_html(html, **kwargs)` function after the markdown processor. This function receives the parsed markdown content as an HTML string in the `html` argument and must return a string with the HTML as filtered.
4. Dactyl runs the `filter_soup(soup, **kwargs)` function after the HTML filters. This function is expected to directly modify the `soup` argument, which contains a [BeautifulSoup 4 object](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) representing the HTML contents.

The keyword arguments (`**kwargs`) for the functions may change in future versions. As of Dactyl 0.5.0, the arguments are as follows:

| Field          | Type       | Description                                    |
|:---------------|:-----------|:-----------------------------------------------|
| `currentpage`  | Dict       | The current page, as defined in the config file plus values inherited from the current target and any processing or calculations. (For example, Dactyl automatically adds a `name` field if one isn't present.) |
| `categories`   | List       | A de-duplicated, ordered list of `category` fields present among pages in this target. |
| `pages`        | List       | A list of page objects for all pages in the current target, in the same order they appear in the config file. |
| `target`       | Dict       | The current target definition, as derived from the config file. |
| `current_time` | String     | The time this build was started. The format is defined by your config's global `time_format` field (in [stftime format](http://strftime.org/)), defaulting to YYYY-MM-DD. |
| `mode`         | String     | Either `html`, `pdf`, or `md` depending on what output Dactyl is building. |
| `config`       | Dict       | The global config object, based on the config file plus any commandline switches. |
| `logger`       | [Logger][] | The logging object Dactyl uses, with the verbosity set to match user input. |

[Logger]: https://docs.python.org/3/library/logging.html#logger-objects


See the [examples](examples/) for examples of how to do many of these things.

## Templates

Dactyl provides the following information to templates, which you can access with Jinja's templating syntax (e.g. `{{ target.display_name }}`):

| Field             | Value                                                    |
|:------------------|:---------------------------------------------------------|
| `target`          | The [target](#targets) definition of the current target. |
| `pages`           | The [array of page definitions](#pages) in the current target. Use this to generate navigation across pages. (The default templates don't do this, but you should.) |
| `currentpage`     | The definition of the page currently being rendered.     |
| `categories`      | A de-duplicated array of categories that are used by at least one page in this target, sorted in the order they first appear. |
| `config`          | The global Dactyl config object. |
| `content`         | The parsed HTML content of the page currently being rendered. |
| `current_time`    | The current date as of rendering. The format is YYYY-MM-DD by default; you can also set the `time_format` field to a custom [stftime format string](http://strftime.org/). |
| `mode`            | The output format: either `html` (default), `pdf`, or `md`. |
| `page_toc`        | A table of contents generated from the current page's headers. Wrap this in a `<ul>` element. |
| `sidebar_content` | (Deprecated alias for `page_toc`.) |

### OpenAPI Spec Templates

When generating docs from an API specification, Dactyl generates a Markdown version for each of these pages first, then uses that as the content for the HTML version as it does when parsing normal Markdown pages. You can use your own templates instead. The templates must use the same filenames as the [built-in OpenAPI templates](dactyl/templates/), which match the pattern `template-openapi_*.md`.

<!-- TODO: Additional documentation on what fields are available to each template. -->
