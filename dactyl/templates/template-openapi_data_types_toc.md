# {{api_title}} Data Types

The following data types are defined for this API:

| Name | Type | Description |
|------|------|-------------|
{%- for title,schema in schemas %}
| [{{title}}]({{type_link(title)}}) | {% if schema.type is defined %}{{schema.type|title}}{% elif schema.oneOf is defined %}{% for t in schema.oneOf %}{% if loop.index > 0 %}, {% endif %}{{t.type|title}}{% endfor %}{% elif schema.allOf is defined %}{% for t in schema.allOf %}{% if loop.index > 0 %}& {% endif %}{{t|title}}{% endfor %}{% elif schema.anyOf is defined %}{% for t in schema.anyOf %}{% if loop.index > 0 %}, {% endif %}{{t|title}}{% endfor %}{% else %}(Not specified){% endif %} | {{schema.description}} |
{%- endfor %}
