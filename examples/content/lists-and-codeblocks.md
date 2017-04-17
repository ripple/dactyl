# Lists and Code Blocks #

Markdown's handling of lists and code blocks is kind of ugly.

## Things that Work ##

Both Dactyl's markdown parser and GitHub's parser handle this case correctly when you use indented (not fenced) code blocks, with some necessary blank lines between.

1. first list item

    Descriptive text inside of 1st list item (indented 4 spaces, after a blank line):

        Indented, non-fenced code block, minimum 8 spaces indented

    More descriptive text inside of 1st list item (indented 4 spaces again):

        Indented, non-fenced code block, minimum 8 spaces indented

2. second list item

For the record, you have to indent everything another 4 spaces if you have a nested list, e.g.:

1. level one list

    1. level two list (4 spaces indented)
    2. level two list item 2

        Some more info on item 2

            a code block inside 2

## Things that don't work ##

1. This is the first item of a list.
```
This is a
    fenced
        code
            block
```
2. The list should resume from here, but it's actually a new list instead
3. Is this the third list item?
    ```
    It still doesn't work if the
        fenced code block
            is itself indented
    ```
4. "Fourth" list item.

    ```
    code fences turn into inline code if you indent them _and_ leave a blank line
    ```
5. Also, don't number your lists with letters in markdown

    a. It won't get interpreted as a list

    b. they get interpreted as raw text

        1. so you can't put more things nested in them

    c. and if you omit a blank line it gets worse
    d. the lines blur together

6. And then the list should resume.
