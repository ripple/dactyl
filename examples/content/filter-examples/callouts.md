# Callouts Demonstration

Callouts are a specially-colored blocks that call attention to particular bits of information. They might be special warnings, asides, or other details. To use callouts, the page (or target) has to have the `callouts` filter enabled, then provide syntax such as the following:

```md
**Tip:** This is a "Tip" callout, styled with green and a checkmark by default.
```

**Tip:** This is a "Tip" callout, styled with green and a checkmark by default.

**Note:** Callouts have four types by default: "Note", "Tip", "Caution", and "Warning".

**Caution:** Be sure not to overuse callouts.

**Warning:** Callouts are very specific. `**Note:**` triggers a callout; `**Notes:**` doesn't. The colon is optional, though.

## Multiline Callouts

> **Tip:** Multiline callouts with blockquotes are now possible.
>
> - Do this to include bulleted lists.
> - Or other types of lists.
>

Code example:

```
> **Tip:** Multiline callouts with blockquotes are now possible.
>
> - Do this to include bulleted lists.
> - Or other types of lists.
>
```

If you have a callout word like **tip** bolded mid-paragraph, it should not become a callout.

> Please **note** that this also applies to blockquotes.

There is a difficult edge case for blockquotes where a paragraph other than the first one starts with a callout keyword:

> This is the start of a blockquote that is not, itself, a callout.
>
> **Note:** This callout occurs in the middle of a blockquote.
>
> But the blockquote containing it is not, itself, a callout.

Also, note that you can cannot use code fences in blockquotes.

> **Caution:** Code fences in blockquotes don't work right.
>
> ```js
> if (true) {
>     console.log('this line of code should be indented');
> }
> ```
>
> The code fence gets treated as inlined code text instead. This is a limitation of Python-Markdown.

You can, however, use indented code blocks in blockquotes:

> **Tip:** To get a proper code block in a blockquote, provide a single
> line of just the blockquote intro `>`, and indent the code block 5 spaces.
>
>     print("Hello world!")
>     if True:
>         print("Note that extra spaces beyond the initial 5 carry over.")
>
> To continue the block quote afterwords, leave a near-blank line similarly.
> Do not use code fences in a blockquote: they don't work as expected.

## Cases to Avoid

* In a list, the callout applies to the whole list item.
    * **Tip:** You can have callouts nested in a list.
        * **Warning:** You probably wouldn't like what happens if you nest callouts in list items that are already callouts.
* One more point. **Note:** The callout doesn't trigger if it's not at the start of the element.

| Table | Stuff |
|-------|-------|
| **Warning:** Callout syntax in table cells is weird. | So it's probably best not to do that. |
| Probably. | **Caution:** It could maybe work better with better CSS. |

## Custom Callout Types

You can define additional callout types if you want. This requires two pieces:

- A list of what words should trigger a callout.
- CSS styles for the relevant callout types.

To define custom callout classes, write the trigger words (case-insensitive) in your project's Dactyl config file. This overwrites the default list, so include the default four if you still want to use them. For example:

```yaml
callout_types:
  - "tip"
  - "ヒント" # equiv. of "Tip" in Japanese (lit. "Hint")
  - "note"
  - "注記" # equiv of "Note" in Japanese
  - "caution"
  - "注意" # equiv. of "Caution" in Japanese
  - "warning"
  - "警告" # equiv. of "Warning" in Japanese
```

Any paragraph that starts with a bold or italic section that consists of _only_ one of the listed words triggers a callout. The callout has two CSS classes:

1. A general callout class. This is `dactyl-callout` by default.
2. The word that triggered the callout (for example, `tip`) in all lowercase.

You can customize the general callout class with a config file line such as the following:

```yaml
callout_class: "my-callout-class"
```

Finally, add the relevant CSS styles to your stylesheet for the new class. For example, the default Dactyl stylesheet defines the "Tip" and "ヒント" callout styles as follows:

```css
.dactyl-content .dactyl-callout {
    border-style: solid;
    border-radius: .25rem;
    border-width: 1px;
        border-left-width: 1px;
    border-left-width: 4px;
    padding: 5px;
        padding-left: 5px;
    padding-left: 25px;
    page-break-inside: avoid;
}

.dactyl-content .dactyl-callout.tip, .dactyl-content .dactyl-callout.ヒント {
    border-color: #28a745; /* Green border */
}

.dactyl-content .dactyl-callout.tip > strong:first-child::before,
.dactyl-content .dactyl-callout.tip > p strong:first-child::before,
.dactyl-content .dactyl-callout.ヒント > strong:first-child::before,
.dactyl-content .dactyl-callout.ヒント > p strong:first-child::before {
    content: "\f058"; /* fontawesome check-circle icon */
    font-family: FontAwesome;
    color: #28a745;
    margin-left: -20px;
    padding-right: 5px;
}
```
