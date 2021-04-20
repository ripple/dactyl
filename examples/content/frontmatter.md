---
desc: This file has Jekyll-style frontmatter
categories: ["Tests", "Dactyl ignores categories beyond the first"]
---
# Frontmatter

Frontmatter is a set of YAML keys and values to start a Markdown file, set off by two lines of `---`. For example, this page has the following frontmatter:

```yaml
---
desc: This file has Jekyll-style frontmatter
categories: ["Tests", "Dactyl ignores categories beyond the first"]
---
```

The frontmatter can be referenced by the preprocessor and by templates. For example:

```
> Description: {{"{{"}}currentpage.desc{{"}}"}}
```

Results:

> Description: {{currentpage.desc}}


**Caution:** If you [include](includes.html) a page, the frontmatter of the included page is not available to the including page.
