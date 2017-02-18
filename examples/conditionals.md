# Conditional Include Test

{% if target.condition == 'tests-2' %}
some text that only appears when tests-2
{% else %}
some text that appears when not tests-2
{% endif %}

some text that always appears
