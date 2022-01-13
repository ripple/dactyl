# Multi Code-Tabs Filter

The multi code-tabs filter lets you list multiple code samples and have them appear as tabs in the HTML version. It looks like this:

<!-- MULTICODE_BLOCK_START -->

*Tab 1 Name*

```json
{
  "id": 2,
  "command": "account_info",
  "account": "r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59",
  "strict": true,
  "ledger_index": "validated"
}
```

*Tab 2 Name*

```json
POST http://s1.ripple.com:51234/
{
    "method": "account_info",
    "params": [
        {
            "account": "r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59",
            "strict": true,
            "ledger_index": "validated"
        }
    ]
}
```

*Tab 3 Name*

```bash
rippled account_info r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59 validated true
```

<!-- MULTICODE_BLOCK_END -->


## Syntax

To display code in tabs, use the following syntax:

    <!-- MULTICODE_BLOCK_START -->

    _First Tab Name_

    ```js
    console.log("First tab contents");
    ```

    _Second Tab Name_

    ```py
    print("Second tab contents")
    ```

    <!-- MULTICODE_BLOCK_END -->

There is no hard limit on the number of tabs you can have. If the total width of the tab names gets too long for the viewscreen, they get broken into multiple lines, which may not look that good depending on your CSS.

Tabs can only contain code blocks, not other contents.

## With Custom Templates

These tabs require some CSS and JavaScript to work:

- [multicode_tabs.js](https://dactyl.link/template_assets/multicode_tabs.js)
- [dactyl-multicode_tabs.css](https://dactyl.link/template_assets/dactyl-multicode_tabs.css)

If you're writing your own templates, you need to include these lines of code in your project to get the tabs to display properly. If you're using the built-in templates, they load this code automatically, so you don't need to do anything special.
