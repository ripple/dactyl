---
parent: usage.html
targets [everything]
---
# Editing

Dactyl supports extended Markdown syntax with the [Python-Markdown Extra](https://pythonhosted.org/Markdown/extensions/extra.html) module. This correctly parses most GitHub-Flavored Markdown syntax (such as tables and fenced code blocks) as well as a few other features.

## Pre-processing

Dactyl pre-processes Markdown files by treating them as [Jinja][] Templates, so you can use [Jinja's templating syntax](http://jinja.pocoo.org/docs/dev/templates/) to do advanced stuff like include other files or pull in variables from the config or commandline. Dactyl passes the following fields to Markdown files when it pre-processes them:

| Field             | Value                                                    |
|:------------------|:---------------------------------------------------------|
| `target`          | The [target](#targets) definition of the current target. |
| `pages`           | The [array of page definitions](#pages) in the current target. Use this to generate navigation across pages. (The default templates don't do this, but you should.) |
| `currentpage`     | The definition of the page currently being rendered. This inherits most fields defined at the target level as well. |
| `categories`      | A de-duplicated array of categories that are used by at least one page in this target, sorted in the order they first appear. |
| `config`          | The global Dactyl config object. |
| `content`         | The parsed HTML content of the page currently being rendered. |
| `current_time`    | The current date as of rendering. The format is YYYY-MM-DD by default; you can also set the `time_format` field to a custom [stftime format string](http://strftime.org/). |
| `mode`            | The output format: either `html` (default), `pdf`, or `md`. |


## Adding Variables from the Commandline

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
