# {{api_title}} Data Types

{% for title,schema in schemas.items() %}
## {{title}}

{{schema.description}}

{% if schema.type is defined %}- **Type:** {{schema.type|title}}
{% elif schema.oneOf is defined %}- **Possible Types:**
{% for option in schema.oneOf -%}
{%- if option.enum is defined %}
    - One of the following {% if option.type is defined %}{{option.type|title}}s{% else %}values{% endif %}:
{%- for suboption in option.enum %}
        - `{{suboption}}`
{%- endfor -%}
{%- else %}
    - {{option.type|title}}
{% endif -%}
{% endfor -%}
{% endif -%}
{%- if schema.enum is defined %}- **Possible Values:**
{%- for option in schema.enum %}
    - `{{option}}`
{%- endfor %}{% endif %}
{% if schema.pattern is defined %}- **Pattern:** `{{schema.pattern}}`
{% endif -%}
{% if schema.example is defined %}- **Example:** `{{schema.example}}`
{% endif -%}

{% if schema.type == "object" and schema.properties is defined %}
This object can contain the following fields:

| Field | Type | Required? | Description |
|-------|------|-----------|-------------|
{%- for name,field in schema.properties.items() %}
| `{{name}}` | {{field.type|title}} | {{"Required" if name in schema.required else "Optional"}} | {% if field.description is defined %}{{field.description}}{% elif "items" in field.keys() %}Array of ***TODO*** {{field["items"]}}{% endif %} |
{%- endfor %}

{% elif schema.type == "array" and schema.items is defined %}
Each member of the array is a ***TODO*** {{schema.items}}
{% endif %}

{% endfor %}
