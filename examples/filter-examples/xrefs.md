# Intelligent Cross-References

Here's some examples for testing. See how they get rendered based on whether the linked page is part of the same target.

[This should link to the callouts demo page.](XREF: filter-callouts.html)

You can link by HTML filename: [ ](XREF: test-lists-and-codeblocks.html)

Or by MD filename: [](XREF:lists-and-codeblocks.md)

If the MD filename is ambiguous, you can specify the full path:
[](xref: filter-examples/xrefs.md)

For an example of an inline cross reference, [](xref:test-gfm-compat.html) should do.

Also, demonstrating that context, spaces, and case mostly don't matter:

  - [](   xReF:   test-includes.html   )
  - (Above this should be a cross-reference to the includes test.)

## Anchors

You can use anchors but the generated labels always use the page name: [](xref:gfm-compat.md#code-blocks)

If you want to refer to a specific anchor, the workaround is to use an explicit label: [Code Blocks](XREF: test-gfm-compat.html#code-blocks)

If the cross-reference appears in multiple targets, Dactyl chooses the first such target listed for the file. For example, if you want to refer to the Conditionals page using the conditionals target (when linking it from the filterexamples target), you have to change the order listed in the config file. Dactyl will always use the "everything" target since that's the first one listed:

[](xref:conditionals.md)

If you want to specify a different target, you have to use conditional text in Jinja templating syntax instead of smart xrefs.
