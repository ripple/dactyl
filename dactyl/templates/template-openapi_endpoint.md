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
The request body takes the form of a
{% endif %}

## Response Format
