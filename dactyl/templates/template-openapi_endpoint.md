# {{operationId}}

{{description}}

## Request Format

```
{{method|upper}} {{path}}
{%- if method in ["post","put","delete"] and requestBody is defined %}

{{(requestBody.content["application/json"].examples.values()|list)[0].value|pprint}}
{% endif %}
```

{% if path_params|length %}
This API method uses the following path parameters:

| Field | Value | Required? | Description |
|---|---|---|---|
{%- for param in path_params %}
| `{{param.name}}` | {% if param.schema.oneOf is defined %}(Varies){% else %}{{param.schema.type|title}}{% endif %} {% if param.schema.title is defined %}([{{param.schema.title}}]({{type_link(param.schema.title)}})){% endif %} | {{"Required" if param.required else "Optional"}} | {{param.description}} |
{%- endfor %}

{% endif %}

{% if query_params|length %}
This API method uses the following query parameters:

| Field | Value | Required? | Description |
|---|---|---|---|
{%- for param in query_params %}
| `{{param.name}}` | {% if param.schema.oneOf is defined %}(Varies){% else %}{{param.schema.type|title}}{% endif %} {% if param.schema.title is defined %}([{{param.schema.title}}]({{type_link(param.schema.title)}})){% endif %} | {{"Required" if param.required else "Optional"}} | {{param.description}} |
{%- endfor %}

{% endif %}

{% if requestBody is defined %}
{{requestBody.description}}

{% if requestBody.content["application/json"].schema is defined %}
{% set req_schema = requestBody.content["application/json"].schema %}
JSON body formatted as a [{{req_schema.title}}]({{type_link(req_schema.title)}})
{% endif %}
{% endif %}

## Response Formats

{% for response_code, response in responses.items() %}
### {{response_code}} {{HTTP_STATUS_CODES[response_code]}}

{{ response.description}}

{% if response.content is defined and response.content["application/json"] is defined and response.content["application/json"].schema is defined %}
{% set resp_schema = response.content["application/json"].schema %}
JSON body formatted as a [{{resp_schema.title}}]({{type_link(resp_schema.title)}})
{% endif %}
{% endfor %}
