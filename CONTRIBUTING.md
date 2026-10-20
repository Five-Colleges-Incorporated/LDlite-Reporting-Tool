# Contributing

# Requirements

This project uses
* python
* pdm
* precious for pre-commit hooks

If you use conda the environment.yaml contains all system level requirements and versions.

# Initial Setup

After cloning the repo install the python dependencies from the lockfile using

```sh
pdm sync
pdm info
```

You might want to setup precious to run as a pre-commit hook.

Add the following to .git/hooks/pre-commit (you might have to create it).

```sh
#!/bin/sh
set -e
precious lint --staged
```

# Running Tests

Tests can be run using pdm scripts which have the correct invocation args.
Additional pytest parameters can be passed on the command line, the most common argument is `-k` for test selectors.

```sh
# Run all tests and display coverage information
pdm run test

# Run non-integration tests without coverage
pdm run-quick

# Run only matching tests and display stdout even for passing tests
pdm run test -s -k 'some_namedtest'
```

# Relocking Dependencies

This repository uses a lock file to ensure builds are reproduceable between development and CI enviroments.
Additionally since this will be installable as a python library a wide range of dependency and python versions must be supported
In the future this may be handled by Tox.

Running

```sh
pdm run lock
```

Will relock the dependencies in three ways
1. With the minimum supported python and dependency versions
1. With the minimum supported python and latest dependency versions
1. With the maximum supported python and latest dependency versions

Variation 2 is the expected environment for development.

Lock files only really need to be regenerated after dependencies are added, major releases of libraries, and changes to supported python versions.
