---
category: Features
parent: features.html
---
# Virtual Pages

"Virtual Pages" are placeholders for pages or websites that are not part of the Dactyl site, but that you want to link from within the Dactyl-generated navigation. Dactyl's built-in templates automatically create links to virtual pages in the appropriate places within the navigation.

Dactyl does not build an associated output HTML file for these pages, so they are linked from PDF builds but their contents are not part of the generated PDF. The [link checker](link-checking.html) treats virtual pages the same as other external links, so it checks links _to_ them but not _in_ the virtual pages.

The "Dactyl Homepage" link listed under this page is an example of a Virtual Page. To create a virtual link, add a stanza such as the following to the page array in your config file:

```yaml
-   name: Dactyl Homepage
    parent: virtual-pages.html
    html: https://dactyl.link/
    targets:
        - everything
```

Specifically, a virtual page is **any page with `//` in its `html` attribute.**

You can also define a virtual page using a `.md` file with [frontmatter](frontmatter.html). For example, you could have a file with the following contents:

```md
---
html: https://dactyl.link/
blurb: This is an example of a virtual page defined by MD frontmatter.
category: Features
parent: virtual-pages.html
---
# Virtual Placeholder

The actual Markdown contents of a "virtual page" are mostly ignored. However, they can be used to provide metadata such as the title and blurb used in navigation on other pages.
```
