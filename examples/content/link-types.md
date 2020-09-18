---
html: link-types.html
parent: tests-index.html
---
# Link Types

This page demonstrates some unusual types of links that you may encounter in HTML or Markdown.

- [Protocol relative URL](//dactyl.link/tests-index.html) - these start with `//` and refer to "whatever protocl is being used now". Dactyl assumes HTTPS should work for these URLs.
- [Mailto URL](mailto:no-reply@dactyl.link) - Email addresses. The link checker ignores these.
- [Javascript Bookmarklet](javascript:alert("A bookmarklet did this")) - JavaScript code embedded in the href directly with `javascript:`. The link checker ignores these.
- [Empty anchor](#) - A link to `#`. The link checker considers these invalid for image `src` attributes but OK for `<a>` tags. They're often used for links that trigger JavaScript events.
