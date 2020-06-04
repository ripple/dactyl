# Dactyl Built-in Templates

This directory contains the default templates included with Dactyl. Starting with v0.11.0, you can include or extend the built-in templates. These templates contain a bunch of useful stuff in modular format, so you can pull in what you need, replace what you don't, and get updates automatically when Dactyl is updated.

Many of the templates work better if you set certain fields on your target or page definitions. Here's a list of those fields:

| Field | Description |
|---|---|
| `prefix` | The base path for this site. Use `/` for a site served from the top-level of its domain. Required for navigation if your site has subfolders or "pretty URLs". |
| `logo` | URL or path for a logo image to use in the top-left. If not defined, uses a text header instead. |
| `google_analytics_tag` | String tag to use with Google Analytics, e.g. "UA-00000000-0". If not defined, doesn't load Google Analytics. |
| `repository` | URL to this site's source repository on GitHub. Required for the "Edit on GitHub" button. |
| `url` | The fully-qualified URL for the base of the site. Required by the sitemap and Google Search templates. |
| `stylesheet` | URL or path to the default stylesheet. The default includes Bootstrap 4.5 as well as custom CSS for code tabs, callouts, and the page layout. See the [styles dir](./dactyl/styles/) for the source SCSS. The default is served by dactyl.link. |
| `dactyljs` | URL or path to the Dactyl JavaScript file to use. This defines "jump to top" and code tab behavior. The default is served by dactyl.link. |
| `bootstrapjs` | URL or path to the Bootstrap JavaScript file to use. The default is served by BootstrapCDN. |
| `fontawesomecss` | URL or path to FontAwesome (v4) CSS file to use. The default is served by BootstrapCDN. |


#### Page Templates

The following built-in templates represent **full pages**, so you can use them with the `default_template:` and `template:` settings in the config file or frontmatter. You can also derive your own templates from these templates using `{% extends 'template' %}` syntax.

| Template | Description |
|---|---|
| `404.html` | Contains an error message intended to be used as a custom 404 page. |
| `base.html` | A general purpose template with a 3-column layout, fixed header, and a footer. The navigation uses the hierarchy (`parent` and `child`) fields introduced by Dactyl v0.10.0. This uses [Bootstrap 4.5.0](https://getbootstrap.com/docs/4.5/). Most of the other built-in templates are derived from this template. |
| `doc.html` | Specialized for individual documents. This is the new default template. The right sidebar has an in-page table of contents, and this runs code tab and syntax highlighting JavaScript by default. (You still need to enable the multicode_tabs filter in your `dactyl-config.yml` file to get code tab syntax.) |
| `landing.html` | A landing page that displays a list of child pages in the center column. |
| `pdf-cover.html` | A cover page and table of contents for PDFs. |
| `redirect.html` | Redirects the user to another URL, as set by the page's `redirect_url` field. Useful for deprecating pages. |
| `simple.html` | A minimal template with no dependencies. |
| `template-sitemap.txt` | A template for a text [sitemap](https://support.google.com/webmasters/answer/183668?hl=en) for use by search engines. |

When extending the default templates, many of them have blocks you can replace. For the full list, inspect the templates' source code in this directory.

##### Sidebars

When using `base.html` or any of the templates derived from it, you can use the `sidebar` field to control the presence of sidebars. By default, both sidebars are present, with the left sidebar containing a cross-page navigation tree and the right sidebar containing an in-page table of contents. Provide `sidebar: disabled` (in the page definition or frontmatter) to have the center column occupy the full width of the page. Use `sidebar: left_only` to show only the left sidebar, and `sidebar: right_only` to show only the right sidebar.

You can replace the sidebar contents by extending `base.html` and putting your replacements in `{% block left_sidebar %}` for the left sidebar, or `{% block right_sidebar %}` for the right sidebar.

On medium viewscreens (768px to 991px wide) the right sidebar becomes full-width and appears before the main contents and left sidebar. On small viewscreens (less than 768px wide) the left sidebar and content become full-width, with the left sidebar coming after the page content. The following ASCII art attempts to depict this relationship:

```text
 Large screens        Medium Screens         Small screens

| L |  C  | R |         | R       |              | R |
|   |     |   |         | L |  C  |              | C |
|   |     |   |         |   |     |              | L |

L = left sidebar
R = right sidebar
C = main content
```


#### Module Templates

The following built-in templates are partial modules you can use with `{% include 'templatehere.html' %}` blocks from other templates. Many of these pieces are used by the page templates above, as well:

| Template | Description |
|---|---|
| `algolia-docsearch.html` | Provides a search box (and accompanying resources) powered by [Algolia DocSearch](https://docsearch.algolia.com/). To use this, you must provide your Algolia API key in the target's `algolia_api_key` field provide your index name in the target's `algolia_index_name` field. |
| `breadcrumbs.html` | Provides [breadcrumbs](https://getbootstrap.com/docs/4.5/components/breadcrumb/) to the current page, based on the hierarchy fields. |
| `children.html` | Displays a bulleted list of children of the current page. You can modify the behavior by setting certain properties before including this template. (See below for an example.) |
| `footer.html` | A footer containing a copyright notice, license link, and language selector (if you have the right fields defined). |
| `github-edit.html` | A button that links to edit the current page's source file on GitHub. Requires the target's `repository` field to be the URL of the site's repository on GitHub. |
| `header.html` | A fixed header containing a logo, navigation to top-level pages, search, and Edit on GitHub buttons if the right fields are defined. |
| `language-dropdown.html` | A language-selector dropdown that points to the equivalent page in other languages, if you have multiple languages defined. (This is the one used in the header.) |
| `language-dropdown.html` | A horizontal language selector that points to the equivalent page in other languages, if you have multiple languages defined. (This is the one used in the footer.) |
| `page-toc.html` | A Bootstrap/ScrollSpy-ready table of contents based on the headers in the current page's Markdown contents. |
| `tree-nav.html` | Tree-style site navigation with collapsible levels. You can set a custom page to be the "top" of the tree to show only a subset of your site. Otherwise it uses the first page (usually the auto-provided cover page) as the top of the tree. Set `nav_omit: true` on a page to hide that page from this navigation. |

##### Children Module

The following demonstrates how to use the `children.html` template to display a list of children of a page (including links):

```html
{% set parent_html = 'some-parent.html' %}
{% set show_blurbs = True %}
{% set depth = 3 %}
{% include 'children.html' %}
```

You can omit any or all of the `{% set ... %}` statements to use the defaults:

| Setting | Description | Default |
|---|---|---|
| `parent_html` | Which page's children to show. The HTML filename of that page. | The current page. |
| `show_blurbs` | If True, add the child page's `blurb` attribute next to its link. | False |
| `depth` | How many levels in the hierarchy to show below the parent. | 5 |

##### Tree Nav Module

The following shows how to display a subset of the tree nav (starting with the file `some_parent.html`) instead of the full tree:

```html
{% set tree_top = pages|selectattr('html', 'defined_and_equalto', 'some_parent.html')|list|first %}
{% include 'tree-nav.html' %}
```
