# Badges

Uses shields.io to make badges out of links. For example:

```md
[badge: orange](http://example.com/ "BADGE_ORANGE")
```

Results in a badge like this:

[badge: orange](http://example.com/ "BADGE_ORANGE")

To make a badge, create a link whose label is `leftside: rightside` (separated by a colon (`:`) character) and set the link's title text to "BADGE_(COLOR)" (all-caps) where "(COLOR)" is one of the following:

* `BRIGHTGREEN`
* `GREEN`
* `YELLOWGREEN`
* `YELLOW`
* `ORANGE`
* `RED`
* `LIGHTGREY`
* `BLUE`
* Any 6-digit hexadecimal color code. For example, `BADGE_006633` for [Color:006633](# "BADGE_006633")
