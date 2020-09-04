# Code Includer

The `include_code` filter provides a function that can make a code sample from a file, pulling in just specific lines if desired.

Call it like so:

```
{{ '{{' }} include_code("sample_include.json", lines="1,3,5-6", mark_disjoint=True) {{ '}}' }}
```

Sample:

{{ include_code("sample_include.json", lines="1,3,5-6", mark_disjoint=True) }}

One range:

{{ include_code("sample_include.json", lines="2-4") }}

The whole file:

{{ include_code("sample_include.json") }}

Custom separator string for disjoint lines:

{{ include_code("sample_include.json", lines="1-2,4-7", mark_disjoint="... (line omitted)...") }}
