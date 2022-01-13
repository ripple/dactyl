---
parent: usage.html
html: elasticsearch.html
targets:
  - everything
---
# ElasticSearch Compatibility

Dactyl has the ability to build JSON formatted for upload to [ElasticSearch](https://www.elastic.co/products/elasticsearch) and even upload it directly.

To build JSON files for upload to ElasticSearch, use the `--es` mode:

```sh
dactyl_build --es
```

This writes files to the usual output directory using an ElasticSearch JSON template. Dactyl skips any files that do not have a `md` source parameter in this mode. The output filenames are the pages' `html` filenames, except ending in `.json` instead of `.html`. You can specify a custom template for these JSON files using the top-level `default_es_template` field in the config file. This template must be a valid JSON file and has several special properties as described in [ElasticSearch JSON Templates](#elasticsearch-json-templates).

Dactyl can also upload these files directly to an ElasticSearch instance, even when building for another mode. For example, to build the HTML version of a target named `filterdemos` but also upload that target's JSON-formatted data to an ElasticSearch instance:

```sh
dactyl_build -t filterdemos --html --es_upload https://my-es-instance.example.com:9200
```

The parameter to `--es_upload` should be the base URL of your ElasticSearch index. You can omit the parameter to use the default base URL of `http://localhost:9200`.


## ElasticSearch JSON Templates

Dactyl has a special format for JSON templates meant for creating ElasticSearch data. These templates must be valid JSON and are processed according to the following rules:

- Any strings in the fields' values are "preprocessed" in a similar context to the Jinja2-based Markdown preprocessor. For example, the string `{{currentpage.name}}` evaluates to the page's name.
- Any object containing the key `__dactyl_eval__` is evaluated as a Python expression. The object is replaced with the results of the expression, with lists becoming JSON arrays and dictionaries becoming JSON objects.
- The above rules apply recursively to values nested in arrays and objects. All other values are preserved literally.

The context provided to the preprocessing and to the `__dactyl_eval__` expressions is the same and contains the following:

| Field           | Python Type | Description                                  |
|:----------------|:------------|:---------------------------------------------|
| `currentpage`   | `dict`      | The current page definition (usually derived from the config file) |
| `target`        | `dict`      | The current target definition (usually derived from the config file) |
| `categories`    | `list`      | A list of unique `category` values used by pages in the current target, in order of appearance. |
| `page_filters`  | `list`      | A list of the names of Dactyl filters applied to the current page. |
| `mode`          | `str`       | Always equal to `es` in this context         |
| `current_time`  | `str`       | The current time, in the `time_format` specified in the config. (Defaults to YYYY-MM-DD) |
| `bypass_errors` | `bool`      | If `true`, this build is running with the option to continue through errors where possible. |
