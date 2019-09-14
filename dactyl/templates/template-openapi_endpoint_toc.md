# {{info.title}} {{info.version}} Methods

{{info.description}}

## API Methods

| Name | Path | Summary |
|:-----|:-----|:--------|
{%- set reflinks = [] -%}
{%- for path,path_def in paths.items() -%}
{%- for method in HTTP_METHODS -%}
{%- if method in path_def.keys() -%}
{%- set endpoint = path_def[method] -%}
{%- set _ = reflinks.append("["+endpoint.operationId+"]: "+method_link(path, method, endpoint) ) %}
| [{{endpoint.operationId}}][] | [`{{method|upper}} {{path}}`][{{endpoint.operationId}}] | {{endpoint.summary}} |
{%- endif %}
{%- endfor %}
{%- endfor %}

{% for reflink in reflinks -%}
{{reflink}}
{% endfor %}
