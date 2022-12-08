# v0.15.3 Release Notes

This release updates the style checker so that style checker overrides apply to the entire page, not just the same block. This means that you don't need to put the override comment in the same line if it applies to a header, and you only need one override if a page uses a discouraged term in an acceptable way across many paragraphs.

In previous releases, you would have to do this:

```
# Discouraged word or phrase here <!-- STYLE_OVERRIDE: discouraged word -->

This paragraph uses the discouraged word or phrase again. <!-- STYLE_OVERRIDE: discouraged word -->
```

In this release, that still works, but you can do this instead:

```
# Discouraged word or phrase here
<!-- STYLE_OVERRIDE: discouraged word -->

This paragraph uses the discouraged word or phrase again, but the override above still applies.
```

This release also reduces the severity level of several log messages, especially for the `dactyl_build` command. The default output is now less noisy.

# v0.15.2 Release Notes

This release updates the style checker to be compatible with pyspellchecker version 0.7.0.

# v0.15.1 Release Notes

This release fixes a bug that made "watch mode" and PDF builds not work on Windows because it assumed that `python3 -m http.server` would launch the simple Python HTTP server on those systems. The updated version should automatically detect the system's Python executable on all platforms.

This release also fixes some broken links in the updated documentation.

# v0.15.0 Release Notes

This release improves OpenAPI spec parsing, adds a new formula for picking default filenames, overhauls Dactyl's own documentation, and fixes the following minor bugs:

- Fixes a bug that caused the default breadcrumbs template to throw an error when the page hierarchy wasn't as expected.
- Fixes a bug where Dactyl would warn about pages not belonging to any targets if the targets those pages belonged to were defined in frontmatter instead of in the config file.

## OpenAPI Spec Parsing

Fixes some bugs where fields were not shown as required in the tables for request bodies and response bodies. Fixes a few other typos in the default templates.

The API endpoint template is now capable of displaying multiple example request bodies and request bodies. (Previously, if you specified multiple response bodies, it could cause Dactyl to fail when trying to build docs from the spec.) If the examples use JSON, the template also applies syntax highlighting by default. The examples are displayed in tabs if the [`multicode_tabs` filter](https://dactyl.link/multicode_tabs.html) is enabled.

A new function, `json_pp()` is available to custom OpenAPI spec templates. This function produces a pretty-printed version of a JSON input.

## "Tail" HTML filename formula

Every HTML file Dactyl builds needs a unique filename to be written to. If you don't specify it in the page definition (example: `html: my-file.html`), Dactyl generates one for you. Previously, you had two options for how to generate filenames from Markdown files: to "flatten" or not. This release adds a new formula, "tail", and changes the config parameter to specify this.


The new option looks like this (put it anywhere in your config file at the top level):

```yaml
default_html_names: tail
# Valid options are "tail", "path", or "flatten". The default is "flatten".
```


With this formula, the generated page names are based on the filename of the source Markdown file _only_. For example, if your input Markdown file was at `usage/editing.md`, the generated filename with each of the formulas would look like this:

| Formula   | Generated HTML Name  |
|:----------|:---------------------|
| `flatten` | `usage-editing.html` |
| `path`    | `usage/editing.html` |
| `tail`    | `editing.html`       |

Some notes on the formulas:

- **flatten**: The default. Use the full path to the md file, except it replaces `/` with `-` so all files end up in one output folder. This is convenient for viewing files locally or zipping them into one big folder.
- **path**: Use the full path to the md file including folders. This results in the output having a folder structure that mirrors the input folder. This can make for prettier URLs, but requires you to handle absolute paths correctly in your templates and hyperlinks.
- **tail**: Use just the filename, not the whole path. This can result in duplicates if you have files with the same name in different folders, for example if you have multiple docs named "overview.md". You should change the duplicates individually using `html` parameters in the page definitions, as needed.


### Backwards Compatibility

The old `flatten_default_html_paths` config parameter is deprecated, but still accepted for backwards compatibility. If set to `true`, it uses the `flatten` formula. (This was and continues to be the default.) If set to `false`, it uses the `path` formula.
