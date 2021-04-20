---
blurb: Dactyl automatically adds syntax highlighting to code blocks.
---
# Code Highlighting

Dactyl automatically adds syntax highlighting to code blocks when it parses Markdown, using the [Pygments](https://pygments.org/)-derived [CodeHilite](https://python-markdown.github.io/extensions/code_hilite/) extension. Parsing the syntax highlighting at compile time like this is faster and less work for readers' computers than in-browser syntax highlighting such as using [highlight.js](https://highlightjs.readthedocs.io/en/latest/api.html). (If you prefer highlight.js's output, though, you can still run it to overwrite Dactyl's syntax highlighting.)

Example of a code segment colored by Dactyl's built-in highlighting:

```py
unacceptable_chars = re.compile(r"[^A-Za-z0-9._ ]+")
whitespace_regex = re.compile(r"\s+")
def slugify(s):
    s = re.sub(unacceptable_chars, "", s)
    s = re.sub(whitespace_regex, "_", s)
    if not s:
        s = "_"
    return s
```

## Requirements

The highlighting requires a stylesheet to define the colors and styles used. Dactyl's default stylesheet includes an example or you can define your own. You can output one of Pygments' default stylesheets from the commandline as in the following example:

```sh
$ pygmentize -S default -f html -a .codehilite > default.css
```

## Languages

Dactyl's code highlighting supports the same [programming languages that Pygments supports](https://pygments.org/languages/). By default it attempts to auto-detect the language, but you can add a language code to the first line of a fenced code block to specify the language.

Example code:

    ```js
    function slugify(s) {
      const unacceptable_chars = /[^A-Za-z0-9._ ]+/
      const whitespace_regex = /\s+/
      s = s.replace(unacceptable_chars, "")
      s = s.replace(whitespace_regex, "_")
      s = s.toLowerCase()
      if (!s) {
        s = "_"
      }
      return s
    }
    ```

Output:

```js
function slugify(s) {
  const unacceptable_chars = /[^A-Za-z0-9._ ]+/
  const whitespace_regex = /\s+/
  s = s.replace(unacceptable_chars, "")
  s = s.replace(whitespace_regex, "_")
  s = s.toLowerCase()
  if (!s) {
    s = "_"
  }
  return s
}
```

## Disabling

If for some reason you want to turn off syntax highlighting, you can add `no_highlighting: true` to your config file at the global, target, or page level.
