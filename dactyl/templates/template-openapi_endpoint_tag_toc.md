# {{info.title}} {{info.version}} {{tag.name|title}} Methods

{{tag.description}}

| Summary | Path |
|:--------|:-----|
{%- for path,method,endpoint in endpoints_by_tag(tag.name) %}
| [{{md_escape(endpoint.summary)}}]({{method_link(path, method, endpoint)}}) | [`{{method|upper}} {{path}}`]({{method_link(path, method, endpoint)}}) |
{%- endfor %}
