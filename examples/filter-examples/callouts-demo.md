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
