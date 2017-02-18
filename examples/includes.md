# Includes Test

This page demonstrates including a file using the preprocessor syntax. The path to including a file is always relative to the **content_path** from the config.

# Includes and Filters

If you include a page that relies on a filter, you might get weird results if the current page / target don't run the filter. For example...

{% include 'filter-examples/callouts-demo.md' %}

# Other Stuff

Lorem ipsum dolor sit amet.
