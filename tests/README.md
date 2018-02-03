# Dactyl Tests

The following files test different parts of Dactyl:

- [testdactyl.py](./testdactyl.py) - Integration tests
- [testdactylbuild.py](./testdactylbuild.py) - Unit tests for `dactyl_build.py`

## Running Integration Tests

Integration tests should be run from the "examples" directory using the following command.

```
python3 ../tests/testdactyl.py
```

These tests should ideally be run prior to any new commit to validate Dactyl's core functions remain intact.

### Writing New Tests

When writing a new test, method names should always start with `test` to ensure they are recognized by the test runner.

Integration tests typically consist of calling `subprocess.call()` or `subprocess.check_call()` to run the appropriate call via command line, followed by an appropriate set of `assert` statements.  Typically, `check_call()` should
be preferred in most cases.  The primary exception to this is if your test is validating that a given command fails.  In this case, running a failing command will result in a CalledProcessError that will automatically fail your test.
You can use `call()` to circumvent this failure, and follow it up with an `assert` statement to validate the appropriate error code (see `test_dactyl_style_checker_with_known_issues` for an example of this).

### Notable Omissions

- Watch Mode: This test case was prioritized as P3, and required some difficult threading implementation to work properly.

## Running Unit Tests

Unit tests should be run from the "tests" directory, to ensure that test config files and mocks are loaded correctly, using the following command.

```
python3 testdactylbuild.py
```

These tests are primarily used to clearly define the behavior of functions defined in [dactyl_build.py](../dactyl/dactyl_build.py), and should ideally be run whenever code is refactored to ensure that behavior remains consistent.