# Commandline Variables

You can provide or override fields of the target using the `--vars` parameter.

For example, the following is the output of `{{"{{target.foo}}"}}`: `{{target.foo}}`

And the following is the output of `{{"{{target.bar}}"}}`: `{{target.bar}}`

Some things to know about these variables:

- `foo` is defined in the config file definition for the "everything" target.
- `bar` is not defined in the config file.

You should be able to change the output of these variables using a `--vars` argument containing either inlined JSON or the filename of a JSON file with the variables to apply to the target. For example:

```sh
dactyl_build --vars '{"foo": "FOO VALUE", "bar": "BAR VALUE"}'
```

or:

```sh
echo '{"foo": "FOO VALUE", "bar": "BAR VALUE"}' > some_vars.json
dactyl_build --vars some_vars.json
```
