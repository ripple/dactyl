---
parent: index.html
category: Filters
section_header: true
template: landing.html
targets:
    - everything
    - filterdemos
---
# Filters

Dactyl supports additional custom post-processing through the use of **filters** which are essentially custom plugins. Filters can operate on the markdown (after it's been pre-processed), on the raw HTML (after it's been parsed), or on a BeautifulSoup object representing the output HTML. Filters can also export functions and values that are available to the preprocessor.

Dactyl comes with several filters, which you can enable in your config file. You can also write your own filters. If you do, you must specify the paths to the folder(s) containing your filter files in the `filter_paths` array of the config file.

To enable a filter for a target or page, set the `filters` field of the config to be an array of filter names, where the filter names are derived from the Python source files in the format `filter_<filtername>.py`. Filter names must be valid Python variable names, so they can't start with a numeral and must contain only alphanumeric and underscore characters.

Dactyl automatically runs the following functions from filter files (skipping any that aren't defined):

1. Before running the preprocessor on a page, Dactyl adds all items from each filter's `export` global dictionary to the preprocessor environment.
2. Dactyl runs the `filter_markdown(md, **kwargs)` function of each filter after the preprocessor. This function receives the preprocessed markdown as a string in the `md` argument and must return a string with the markdown as filtered.
3. Dactyl runs the `filter_html(html, **kwargs)` function after the markdown processor. This function receives the parsed markdown content as an HTML string in the `html` argument and must return a string with the HTML as filtered.
4. Dactyl runs the `filter_soup(soup, **kwargs)` function after the HTML filters. This function is expected to directly modify the `soup` argument, which contains a [BeautifulSoup 4 object](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) representing the HTML contents.

The keyword arguments (`**kwargs`) for the functions may change in future versions. As of Dactyl 0.5.0, the arguments are as follows:

| Field          | Type       | Description                                    |
|:---------------|:-----------|:-----------------------------------------------|
| `currentpage`  | Dict       | The current page, as defined in the config file plus values inherited from the current target and any processing or calculations. (For example, Dactyl automatically adds a `name` field if one isn't present.) |
| `categories`   | List       | A de-duplicated, ordered list of `category` fields present among pages in this target. |
| `pages`        | List       | A list of page objects for all pages in the current target, in the same order they appear in the config file. |
| `target`       | Dict       | The current target definition, as derived from the config file. |
| `current_time` | String     | The time this build was started. The format is defined by your config's global `time_format` field (in [stftime format](http://strftime.org/)), defaulting to YYYY-MM-DD. |
| `mode`         | String     | Either `html`, `pdf`, or `md` depending on what output Dactyl is building. |
| `config`       | Dict       | The global config object, based on the config file plus any commandline switches. |
| `logger`       | [Logger][] | The logging object Dactyl uses, with the verbosity set to match user input. |

[Logger]: https://docs.python.org/3/library/logging.html#logger-objects
