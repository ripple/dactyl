# Includes Test

This page demonstrates including a file using the preprocessor syntax. The path to including a file is always relative to the **content_path** from the config.

# Includes and Filters

If you include a page that is written to use a filter, you might get weird results if the current page / target don't run the filter. For example...

{% include 'filter-examples/callouts.md' %}

# Other Stuff

Includes are part of preprocessing, so you can do things like making one file that has all your [Markdown reference links][], and including that in all your pages to make the reference links always available.

[Markdown reference links]: https://daringfireball.net/projects/markdown/syntax#link

Reader exercise: make your own filter to automatically include a page at the end of another page!
