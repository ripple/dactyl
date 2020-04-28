# Callouts Demonstration #

**Tip:** Callouts are a great way to call attention to particular bits of information.

In order to use callouts, the page (or target) has to have the `callouts` filter enabled.

**Note:** Callouts have four types, "Note", "Tip", "Caution", and "Warning".

**Caution:** Be sure not to overuse callouts.

**Warning:** Callouts are very specific. `**Note:**` triggers a callout; `**Notes:**` doesn't.


## Finer points

**Tip** The colon is optional, though.

* **Note:** Callouts can only contain a single element of text. You can't have multiple paragraphs or a list nested in a callout.
* The callout applies to the whole list item.
    * **Tip:** You can have callouts nested in a list.
        * **Warning:** Don't nest callouts in list items that are already callouts, because that's ugly and confusing.
* And more stuff. **Note:** The callout doesn't trigger if it's not at the start of the element.

| Table | Stuff |
|-------|-------|
| **Warning:** Callout syntax in table cells is weird. | So it's probably best not to do that. |
| Probably. | **Caution:** It could maybe work better with better CSS. |

> **Tip:** Multiline callouts with blockquotes are now possible.
>
> - Do this to include bulleted lists.
> - Or other types of lists.
>

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
