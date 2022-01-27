---
category: Filters
parent: filters.html
filters:
    - buttonize
    - external_links
---
# External Links

This filter adds an "external link" icon to [links to outside websites](https://en.wikipedia.org/wiki/Hyperlink). Well, it's not actually all that smart. It doesn't know what website it's on, so it adds the icon to any link whose URL starts with `http:` or `https:`. It also sets all external links to open in a new tab/window.

A [link to another page](filters.html) won't have the icon.

If you try to combine this filter with the [button links filter >](https://dactyl.link/buttonize.html), make sure **buttonize runs first**. Otherwise, external links will not get styled as buttons when intended.
