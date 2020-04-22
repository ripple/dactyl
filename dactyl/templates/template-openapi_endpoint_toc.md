# {{info.title}} {{info.version}} Methods

{{info.description}}

{% if tags %}
View API methods by category:

{% for tag in tags %}
- [{{tag.name|title}} Methods](#{{slugify(tag.name)|lower}}-methods)
{% endfor %}
{% endif %}

{% for tag in tags %}
{% if endpoints_by_tag(tag.name)|list|length %}
## {{tag.name|title}} Methods

{{tag.description}}

| Summary | Path |
|:--------|:-----|
{%- for path,method,endpoint in endpoints_by_tag(tag.name) %}
| [{{endpoint.summary}}]({{method_link(path, method, endpoint)}}) | [`{{method|upper}} {{path}}`]({{method_link(path, method, endpoint)}}) |
{%- endfor %}

{% endif %}
{% endfor %}

{% if endpoints_by_tag("Uncategorized")|list|length %}
## Uncategorized Methods

| Name | Path | Summary |
|:-----|:-----|:--------|
{%- set reflinks = [] -%}
{%- for path,method,endpoint in endpoints_by_tag("Uncategorized") %}
{%- set _ = reflinks.append("["+endpoint.operationId+"]: "+method_link(path, method, endpoint) ) %}
| [{{endpoint.operationId}}][] | [`{{method|upper}} {{path}}`][{{endpoint.operationId}}] | {{endpoint.summary}} |
{%- endfor %}

{% for reflink in reflinks -%}
{{reflink}}
{% endfor %}

{% endif %}
