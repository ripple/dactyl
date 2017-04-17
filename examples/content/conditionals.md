# Conditional Include Test

{% if target.condition == 'tests-2' %}
some text that only appears when tests-2
{% else %}
some text that appears when not tests-2
{% endif %}

some text that always appears

{% if mode=="pdf" %}
This is PDF mode.
{% elif mode=="html" %}
This is HTML mode.
{% elif mode=="md" %}
This is MD mode (See also: `--githubify`)
{% else %}
We should not reach this case.
{% endif %}
