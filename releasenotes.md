# v0.13.2 Release Notes

This release adds "hover anchors" and fixes two bugs with filters and frontmatter.

## Bug Fixes

- Fixed a problem with the `export` values of filters not being loaded when those filters were enabled via frontmatter on some pages.
- Fixed a problem where filters would not get imported if they were only listed in frontmatter sections and not in the main config file somewhere.

### Hover Anchors

Added the option to enable "hover anchors" for linking directly to headers. These are little links that appear next to a header so that you can right-click and copy the link to get a URL directly to that header. To enable hover anchors, you need to make two changes:

1. In your Dactyl config file, add a `hover_anchors` field to the definition of the target(s) or page(s) you want to enable them on. Set the value to whatever text or HTML you want to represent the anchor. Some examples:

    Plain text octothorpe:

        -   name: some_target
            hover_anchors: "#"

    FontAwesome 4 link icon:

        -   name: some_target
            hover_anchors: <i class="fa fa-link"></i>

2. In your stylesheet, add styles to show `.hover_anchor` elements only when headers are hovered. For example:

    CSS:

        .hover_anchor {
          visibility: hidden;
          padding-left: 1rem;
          font-size: 60%;
          text-decoration: none;
        }

        h1:hover .hover_anchor, h2:hover .hover_anchor,
        h3:hover .hover_anchor, h4:hover .hover_anchor,
        h5:hover .hover_anchor, h6:hover .hover_anchor {
          visibility: visible;
        }

    Or, SCSS, if you prefer:

        .dactyl_content {
          // Hover anchors ---------------
          .hover_anchor {
            visibility: hidden;
            padding-left: 1rem;
            font-size: 60%;
          }

          h1,h2,h3,h4,h5,h6 {
            &:hover .hover_anchor {
              visibility: visible;
              text-decoration: none;
            }
          }
        }



# v0.13.1 Release Notes

This release fixes the link checker's handling of some less common hyperlink types. It also adds the `--legacy_prince` option to allow you to build PDFs with Prince version 10 and earlier.

# v0.13.0 Release Notes

This release adds built-in (compile-time) syntax highlighting to Dactyl. This syntax highlighting runs by default, but you can disable it with `no_highlight` in your config file (at the global, target, or page level). The built-in templates now use the built-in highlighting at compile time instead of doing syntax highlighting browser-side.

This release also includes some documentation improvements.


# v0.12.0 Release Notes

This release introduces significant upgrades to the Dactyl Style Checker. Specifically:

- The style checker now does spell-checking.
    - To add words to the spell checker's dictionary, add a `spelling_file` to your config. This value should point at a text file where each line contains a single word (case-insensitive) to add to the dictionary. You can also exempt words from a specific page with a comment such as `<!-- SPELLING_OVERRIDE: word1, word2 -->`.
- The style checker now measures and reports on pages' readability according to some common readability score numbers. You can set goals for readability at the target level or for individual pages. Note that readability scores are not a reliable measure of actual readability. For example, scores for the exact same document may vary based on how Dactyl normalizes the content to plain text. Readability scores do not affect the style checker's pass/fail results unless you set goals.
- The style checker also reports some metrics on the length of given pages. This does not contribute to the style checker's pass/fail reports, but may be useful in finding pages that are too long or short.

For more information on how to use these features, see the [README](README.md).

There are no changes to `dactyl_build` or `dactyl_link_checker` in this release.
