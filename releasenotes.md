# v0.10.2 Release Notes

Fixes a bug that caused ElasticSearch uploads to fail.

# v0.10.1 Release Notes

Fixes a bug that caused Dactyl to fail on Python 3.5.

# v0.10.0 Release Notes

Dactyl v0.10.0 is a major refactor of Dactyl that includes some breaking changes and new functionality.

## Breaking Changes

Dactyl v0.10.0 contains two significant breaking changes: a new header ID formula, and xref errors.

### Header ID Formula

The default formula for header IDs has changed slightly. Most headers in English documents have the same IDs as before, but headers may have different IDs in certain edge cases, especially for headers with non-English text. In cases where your content contains an anchor link to a header whose ID has changed, you must update your links to use the header's ID under the new formula.

The new formula more closely matches GitHub's formula for header IDs. In particular:

- The new formula does not strip accents from characters such as é or ç.
- The new formula does not strip East Asian script (nor other "word" characters from Unicode).
- For repeated headers, the new formula appends `-1`, `-2`, etc. instead of `_1`, `_2`, etc.

The only known divergences from GitHub's header formula are in cases where GitHub creates invalid `id` values.

With this change, the `standardize_header_ids` filter is **DEPRECATED**. It will be removed in a future version.

### xrefs Errors

The `xrefs` filter now raises an error if you link to a page without providing link text, but that page's name is unknown.

Previously the filter would silently provide link text based on other attributes of the page, such as its markdown filename. This is usually not what you want the final output to have.

To continue building despite these types of errors, pass `--bypass_errors` when running `dactyl_build`. Preferably, fix the xrefs so the referenced pages have proper names.


## New Features

### Frontmatter Improvements

Dactyl v0.10.0 improves the handling of Jekyll-style frontmatter. Frontmatter is metadata at the start of a Markdown file, surrounded by a pair of `---` lines. Now you can provide any of a page's fields in the frontmatter instead of in the Dactyl config file, except for the path to the file itself.

In cases where the config file and the frontmatter specify conflicting values for a field, the config file takes precedence.

Example of a page with frontmatter:

**File: `concept1.md`**

```md
---
category: Concepts
parent: concepts.html
targets:
    - en
---
# Placeholder Concept 1

This is the content of the placeholder concept page.
```

**Dactyl Config entry:**

```yaml
-   md: content/concept1.md
    category: Placeholders # Optional; Overrides "category" from the frontmatter
```

### New Hierarchy Features

Managing a hierarchy of documents is a common problem, so the new version of Dactyl makes this easier with some new fields for defining your pages' hierarchy.

Add the **`parent` field** to a page's metadata to define a "parent" for the current page. The value of the `parent` field should be **the exact value of the parent page's `html` field.** If a page doesn't have an explicitly-specified `html` value, you must use the automatically generated value for the parent.

Example:

```yaml
- md: some-parent-page.md
  html: parent.html

- md: first-child-page.md
  html: child1.html
  parent: parent.html

- md: grandchild.md
  html: grandchild.html
  parent: child1.html

- md: child2.md
  html: child2.html
  parent: parent.html
```

This creates a conceptual hierarchy like this:

- `parent.html`
    - `child1.html`
        - `grandchild.html`
    - `child2.html`

After loading pages, Dactyl provides the following additional fields in each page's metadata, which are available to the preprocessor, filters, and templates:

| Field            | Value    | Description                                    |
|:-----------------|:---------|:-----------------------------------------------|
| `children`       | List     | A list of pages that claim this page as a parent. Each page in the list is provided as a reference, so you can read its metadata including following its own children. |
| `is_ancestor_of` | Function | A function you can use to check whether a given page is the direct or indirect parent of another given page. Provide the exact `html` of the page you want to check for as the single argument to this function. |

This conceptual hierarchy does not affect the paths where output files are written. (It would be sensible to choose output `html` paths to reflect this hierarchy, though.) Also, Dactyl does not enforce a strict tree-like hierarchy of parents/children. It is up to the templates to use these fields to provide appropriate navigation elements based on the hierarchy these fields represent. [Example of template for printing page hierarchy tree.](https://github.com/mDuo13/dactyl-starter-kit/blob/master/template/template-tree-nav.html)

**Caution:** It is possible to create infinite loops. Do not make a page its own direct or indirect parent. Doing so is likely to result in a `RecursionError` when trying to build.


### Other New Fields

In addition to the new page fields added for page hierarchy, Dactyl now provides certain fields to every page based on the results of parsing that page. Previously, Dactyl only provided these fields when building ElasticSearch JSON formats. Now, Dactyl provides these fields to every page after parsing that page's content Markdown. These fields are:

| Field       | Value      | Description                                       |
|:------------|:-----------|:--------------------------------------------------|
| `blurb`     | String     | An excerpt from the start of the page, if available, generally consisting of the first paragraph of body text. |
| `plaintext` | String     | The entire body text of the page, stripped of any formatting. |
| `headermap` | Dictionary | A mapping, where the keys are the headers' plain text (formatting removed) and the values are those headers' unique IDs. |

Because these fields are derived from the content's HTML output, they are **not available** to the preprocessor, nor in filter functions `filter_markdown()` or `filter_html()`. They **are available** to `filter_soup()` functions and when rendering HTML templates.

If a page already has a `blurb` field defined in its metadata, Dactyl leaves the existing value in place.

### New headers map

Dactyl already provided templates with a string containing the HTML for a list of header-based anchors in the current page, in the `page_toc` variable. (This variable, and its legacy alias `sidebar_content`, continue to be available.) However, to provide an opportunity to customize the markup of how the in-page anchors are presented, Dactyl now also provides a `headers` field, which you can use to generate a more customized table of contents. (For example, if you are using Bootstrap, you can use this to provide the classes necessary to make Scrollspy work properly.)

The `headers` field is a **list of headers** in the document, derived from `<h1>` through `<h6>` elements. **Each header** in the list is a dictionary with the following fields:

| Field   | Value   | Description                                              |
|:--------|:--------|:---------------------------------------------------------|
| `text`  | String  | The plain text of the header, with formatting removed.   |
| `id`    | String  | The unique ID of the header element in the HTML. You can use this to link to it. |
| `level` | Integer | The level of this header. `<h1>` elements are level 1, `<h2>` elements are level 2, and so on. |

Note that while `page_toc` only contains headers of level 3 and above, `headers` contains headers all the way down to `<h6>` elements, so your template can choose whether to print them or not.

See the following examples for a comparison:

**Old Style:**

```html
No customization of the content (but still works)
<ul class="your-class">
  {{page_toc}}
</ul>

Results in:
<ul class="your-class">
  <li class="level-1"><a href="#top-header">Top header</a></li>
  <li class="level-2"><a href="#lower-header">Lower header</a></li>
  <li class="level-2"><a href="#next-header">Next header</a></li>
</ul>
```

**New Style:**

```html
Can set custom classes or even use different HTML elements:
<nav class="your-class">
  {% for h in headers %}
    <a class="nav-item level-{{h.level}}" href="#{{h.id}}">{{h.text}}</a>
  {% endfor %}
</nav>

Results in:
<nav class="your-class">
    <a class="nav-item level-1" href="#top-header">Top header</a>
    <a class="nav-item level-2" href="#lower-header">Lower header</a>
    <a class="nav-item level-2" href="#next-header">Next header</a>
</nav>
```


### Path Filenames

Previously, the `html` value for a file had to be a filename writable in the filesystem. You can now specify an `html` value ending in `/` as a shortcut for a filename ending in `index.html`. This should make it easier to create "pretty URLs" without any special server configuration.

Furthermore, the built-in xrefs filter now supports adding a prefix to the generated links, so that you can use it to provide absolute, not relative paths. To use this, add a `prefix` field to your target definition. For example, if you publish a `docs` target at `example.com/docs/`, set the prefix as follows:

```yaml
targets:
  -   name: docs
      display_name: Example Documentation
      prefix: "/docs/"
```

If you publish the target at the root level of a domain, use the prefix `"/"`.

In future releases, Dactyl may use the `prefix` field for more conveniences around absolute paths.


### Internationalization Improvements

Dactyl now supports `{% trans %}Text to be translated{% endtrans %}` syntax in templates.

To use translated values for these strings, add the following field to a **target definition**:

| Field         | Value  | Description                                         |
|:--------------|:-------|:----------------------------------------------------|
| `locale_file` | String | Path to a (binary) `.mo` file containing translated strings for this target's locale/language. |

Support for locale files is ***experimental*** and the details are likely to change in a future version of Dactyl.

You can use [Babel](http://babel.pocoo.org/) to extract strings from templates and to compile the translations into a `.mo` file. For an example, see <https://github.com/mDuo13/dactyl-starter-kit/blob/master/locale/README.md>.


### OpenAPI Parsing Improvements

This release improves several aspects of OpenAPI (Swagger) specification parsing.

- Single `example` requestBody values for API methods now display properly in the method detail page. Previously Dactyl only printed an example requestBody if the method definition used the `examples` array.
- Example requestBody and Data Type are now formatted as pretty-printed JSON by default.
- Fixed handling of schema names containing special characters such as `[` and `]`.

However, OpenAPI spec parsing should still be considered experimental.

### Multiline Callouts

The built-in callouts filter now supports multi-line callouts using Markdown's blockquote syntax. A blockquote must be set off from paragraph text by blank lines before and after. Within the blockquote, each line must start with `> `. (The space is optional but recommended.) For example:

```md
Some paragraph text.

> **Tip:** This begins a multiline callout.
>
> - It can have lists.
>     - Indentation does not count the space in the `> ` as part of its
>       requirements, so things that would normally need to be indented 4 spaces
>       must be indented 5 instead.
> - That's just Markdown syntax for you.

More paragraph text
```

Build the [examples](examples/) to see it in action and to see some samples of specific edge cases.

## Bug Fixes and Other Cleanup

- `--skip_preprocessor` (when using a config file) works again. It had been broken since v0.40.0.
- `--bypass_errors` can now bypass errors that occurred when running a filter.
- Removed some extraneous whitespace in the default tables of contents `{{page_toc}}`.
- Improved the clarity of log messages.
- New unit tests.
