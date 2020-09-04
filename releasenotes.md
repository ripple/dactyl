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
