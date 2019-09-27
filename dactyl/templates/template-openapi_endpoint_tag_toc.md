# {{info.title}} {{info.version}} {{tag.name|title}} Methods

{{tag.description}}

| Summary | Path |
|:--------|:-----|
{%- set reflinks = [] -%}
{%- for path,method,endpoint in endpoints_by_tag(tag.name) %}
{%- set _ = reflinks.append("["+endpoint.summary+"]: "+method_link(path, method, endpoint) ) %}
| [{{endpoint.summary}}][] | [`{{method|upper}} {{path}}`][{{endpoint.summary}}] |
{%- endfor %}

{% for reflink in reflinks -%}
{{reflink}}
{% endfor %}
