# Hierarchy Demo

This page demonstrates how you can use Dactyl's built-in hierarchy features to generate a table of contents automatically.

Source:

```jinja
<ul>
{{"{%"}} macro page_w_children(pg) {{"%}"}}
  <li class="dactyl-toc-entry"><a href="{{"{{"}} pg.html {{"}}"}}">{{"{{"}} pg.name {{"}}"}}</a></li>
  {{"{%"}} if pg.children {{"%}"}}
    <ul>
      {{"{%"}} for child in pg.children {{"%}"}}
        {{"{{"}} page_w_children(child) {{"}}"}}
      {{"{%"}} endfor {{"%}"}}
    </ul>
  {{"{%"}} endif {{"%}"}}
{{"{%"}} endmacro {{"%}"}}

{{"{%"}} for page in pages {{"%}"}}
  {{"{%"}} if page.parent is undefined {{"%}"}}
    {{"{{"}} page_w_children(page) {{"}}"}}
  {{"{%"}} endif {{"%}"}}
{{"{%"}} endfor {{"%}"}}
</ul>
```

Results:
