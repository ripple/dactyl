# Includes Test

This page demonstrates including a file using the [preprocessor's `include` syntax](https://jinja.palletsprojects.com/en/2.11.x/templates/#include). The path to including a file is always relative to the **`content_path`** from the config.

Example code:

```
{{"{%"}} include 'includes/reusable.md' {{"%}"}}
```

Results:

{% include 'includes/reusable.md' %}

## With Conditionals

Sometimes you want to use a block of text with slight differences in different contexts. You can use [conditionals](conditionals.html) to define the different text to appear or not depending on where the file is being included. In most cases you can check some property of the `currentpage` or `target`, but in case you can't, the [`set` tag](https://jinja.palletsprojects.com/en/2.11.x/templates/#assignments) can help.

Example code:

```
{{"{%"}} set extended = True {{"%}"}}
{{"{%"}} include 'includes/reusable.md' {{"%}"}}
```

Results:

{%  set extended = True %}
{%  include 'includes/reusable.md' %}



# Includes and Filters

If you include a page that is written to use a filter, you might get weird results if the current page / target don't run the filter.

# Other Stuff

Includes are part of preprocessing, so you can do things like making one file that has all your [Markdown reference links][], and including that in all your pages to make the reference links always available.

[Markdown reference links]: https://daringfireball.net/projects/markdown/syntax#link

Reader exercise: make your own filter to automatically include a page at the end of another page!
