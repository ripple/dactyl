# v0.14.3 Release Notes

This release adds compatibility with Jinja 3.x and includes two minor improvements to the style checker:

- No longer attempts to check inlined SVG elements. (This caused false reports of misspelled words when the SVG contained text elements without whitespace between them.)
- Spelling file can now contain comments starting with `#`. (Only lines _starting_ with `#` are treated as comments.)


# v0.14.2 Release Notes

This release fixes a couple bugs in the built-in templates when using virtual pages with a `prefix` value. It also changes to use the `prefix` value inherited at the page level so that individual pages can overwrite the value if necessary. (A 404 page, for example, might want to use a separate prefix since it may be used at different paths.)


# v0.14.1 Release Notes

This release removes a couple of debug statements that broke compatibility with Python 3.5. (Python 3.5 has reached end of life, but Dactyl still works with it for now if you use the right versions of its dependencies.)

# v0.14.0 Release notes

This release improves the built-in templates, improves the documentation in the examples, and introduces the concept of "Virtual Pages". Virtual pages are placeholders for links to external sites, which you can insert into the automatically-generated navigation with a stanza similar to a page built by Dactyl.

To add a Virtual Page, add a page to your config with an `html` value containing `//`. For example,

```yaml
-   name: Dactyl Homepage
    blurb: Go to the online home of Dactyl.
    html: https://dactyl.link/
    parent: virtual-pages.html
    targets:
        - everything
```

Dactyl's built-in templates automatically add the page to generated navigation. Use the `parent` field to specify where in the hierarchy the virtual page should appear. The page also shows up as an item in the page lists for the preprocessor and templates so custom templates and pages can list it also.

## Breaking Changes

Most projects using Dactyl won't experience breaking changes from this release, but the following changes may potentially require action in certain circumstances:

- The `buttonize` filter now uses Bootstrap's `btn btn-primary` classes instead of adding a `button` class.
- The built-in `tree-nav.html` template and its associated CSS have been significantly updated to fix bugs with deeper levels of navigation and to simplify the generated HTML.
- The `children.html` template no longer omits blurbs beyond the top level by default.

## Other Changes

- The default PDF templates (`simple.html` and `pdf-cover.html`) better handle frontmatter and hierarchy fields.
- The SCSS for the tree nav has been split into a separate file to make it easier to include in external projects.
- Updated many of the examples including their URLs.
- Fixed integration test for the style checker.
