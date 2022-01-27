# Conditionals

You can use the preprocessor to hide or show certain content based on various conditions. For example, you can have a page used in multiple targets, but omit certain portions from the output in some targets. Or, you can have text and markup that only shows up in HTML mode but not PDF mode or similar rules.

You can use any of [the fields available to the preprocessor](https://github.com/ripple/dactyl/#pre-processing) for your conditionals, including [commandline variables](cli-vars.html) and any fields defined in the [frontmatter](frontmatter.html).

Example of printing different text by :

{# Note, if you're looking at the Markdown file: we're escaping the Jinja syntax here so that it looks good in the output. #}

```jinja2
{{"{% if currentpage.condition == 'tests-2' %}"}}
some text that only appears when the "condition" field of the current page is "tests-2"
{{"{% else %}"}}
some text that appears when not tests-2
{{"{% endif %}"}}

some text that always appears
```

Result:

{% if currentpage.condition == 'tests-2' %}
some text that only appears when the "condition" field of the current page is "tests-2"
{% else %}
some text that appears when not tests-2
{% endif %}

some text that always appears

---

Example of printing different text in different

```jinja2
{{"{% if mode == 'pdf' %}"}}
This is PDF mode.
{{"{% elif mode == 'html' %}"}}
This is HTML mode.
{{"{% elif mode == 'md' %}"}}
This is MD mode (See also: `--githubify`)
{{"{% elif mode == 'es' %}"}}
This is ElasticSearch indexing mode (JSON).
{{"{% else %}"}}
We should not reach this case.
{{"{% endif %}"}}
```

Result:

{% if mode == 'pdf' %}
This is PDF mode.
{% elif mode == 'html' %}
This is HTML mode.
{% elif mode == 'md' %}
This is MD mode (See also: `--githubify`)
{% elif mode == 'es' %}
This is ElasticSearch indexing mode (JSON).
{% else %}
We should not reach this case.
{% endif %}
