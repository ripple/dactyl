---
html: link-checking.html
parent: features.html
---
# Link Checking

Dactyl includes a link-checking script to automatically detect and report on broken hyperlinks in your generated documentation.

## Usage

First, build some documentation to an output path. Depending on your configuration, you may want to build multiple targets to different output directories before running the link checker.

Then, run the link checker as follows:

```sh
$ dactyl_link_checker
```

This checks all the files in the output directory for links and confirms that any HTTP(S) links, including relative links to other files, are valid. For anchor links, it checks that an element with the correct ID exists in the target file. It also checks that the `src` of all image tags exists.

If there are links that are always reported as broken but you don't want to remove (for example, URLs that block Python's user-agent) you can add them to the `known_broken_links` array in the config.

In quiet mode (`-q`), the link checker still reports in every 30 seconds just so that it doesn't get treated as stalled and killed by continuous integration software (e.g. Jenkins).

To reduce the number of meaningless failure reports (because a particular website happened to be down momentarily while you ran the link checker), if there are any broken remote links, the link checker waits 2 minutes after finishing and then retries those links in case they came back up. (If they did, they're not considered broken for the link checker's final report.)

You can also run the link checker in offline mode (`-o`) to skip any remote links and just check that the files and anchors referenced exist in the output directory.

If you have a page that uses JavaScript or something to generate anchors dynamically, the link checker can't find those anchors (since it doesn't run any JS). You can add such pages to the `ignore_anchors_in` array in your config to skip checking for links that go to anchors in such pages.

## Unusual Link Types

Some unusual types of links that you may encounter in HTML or Markdown include:

- [Protocol relative URL](//dactyl.link/features.html) - these start with `//` and refer to "whatever protocl is being used now". Dactyl assumes HTTPS should work for these URLs.
- [Mailto URL](mailto:no-reply@dactyl.link) - Email addresses. The link checker ignores these and other links that use other URI schemes.
- [Javascript Bookmarklet](javascript:alert%28'A bookmarklet did this'%29) - JavaScript code embedded in the href directly with `javascript:`. The link checker ignores these.
- [Empty anchor](#) - A link to `#`. This type of link is often used to trigger JavaScript events. The link checker considers these invalid for `<img>` paths but OK for `<a>` tags.
