---
desc: This file has Jekyll-style frontmatter
categories: ["Tests", "Dactyl ignores categories beyond the first"]
title: Page With Frontmatter
---
# Page That Has Frontmatter

This page demonstrates a file that contains frontmatter.

The frontmatter can be referenced by the preprocessor. For example:

```
Description: {{"{{"}}currentpage.desc{{"}}"}}
```

Results:

> Description: {{currentpage.desc}}
