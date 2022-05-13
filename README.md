# Manifestoo

[![Github-CI][github-ci]][github-link]
[![Coverage Status][codecov-badge]][codecov-link]
[![PyPI][pypi-badge]][pypi-link]

<!--- shortdesc-begin -->

A tool to reason about [Odoo](https://odoo.com) addons manifests.

<!--- shortdesc-end -->

## Installation

<!--- install-begin -->

Using [pipx](https://pypi.org/project/pipx/) (recommended):

```console
pipx install manifestoo
```

Using [pip](https://pypi.org/project/pip/):

```console
pip install --user manifestoo
```

<!--- install-end -->

## Features

<!--- features-begin -->

Manifestoo is a command line tool that provides the following features:

* listing addons,
* listing modified or new addons on a feature branch,
* listing direct and transitive dependencies of selected addons,
* listing direct and transitive co-dependencies of selected addons,
* listing core Odoo CE and EE addons,
* listing external dependencies,
* listing missing dependencies,
* displaying the dependency tree,
* checking license compatibility,
* checking development status compatibility.

For a full list of commands an options, run `manifestoo --help`.

For more information, read the [documentation](https://manifestoo.readthedocs.io/en/stable).

<!--- features-end -->

## Quick start

<!--- quickstart-begin -->

Let's create a directory (`/tmp/myaddons`) containing addons `a`, `b` and `c`,
where `a` depends on `b` and `c`, and `b` and `c` respectively depend on the
`contacts` and `mail` core Odoo modules.

Using `bash` you can do it like this:

```console
mkdir -p /tmp/myaddons/{a,b,c}
echo '{"name": "A", "version": "14.0.1.0.0", "depends": ["b", "c"], "license": "GPL-3"}' > /tmp/myaddons/a/__manifest__.py
echo '{"name": "B", "version": "14.0.1.0.0", "depends": ["crm"], "license": "Other Proprietary"}' > /tmp/myaddons/b/__manifest__.py
echo '{"name": "C", "version": "14.0.1.0.0", "depends": ["mail"], "license": "LGPL-3"}' > /tmp/myaddons/c/__manifest__.py
```

It is possible to select modified addons compared to a target branch `target`.

```console
$ manifestoo --addons-path /tmp/myaddons --select-git-modified target list
a
b
c
```
To instead get only newly added addons, use (shortcut `-n`):
```console
$ manifestoo --addons-path /tmp/myaddons --select-git-new target list
c
```

The manifestoo `list` command is useful to list all installable addons in a
directory. This can be useful to install them all at once, for instance.

```console
$ manifestoo --select-addons-dir /tmp/myaddons list
a
b
c
```

The `list-depends` command shows the direct dependencies. It is handy to
pre-install a database before running tests.

```console
$ manifestoo -d /tmp/myaddons list-depends --separator=,
crm,mail
```

The `list-codepends` command shows the transitive co-dependencies.
It is handy to know which modules are impacted by changes in selected modules.

```console
$ manifestoo --addons-path /tmp/myaddons --select a list-codepends --separator=,
b,c
```

You can explore the dependency tree of module `a` like this:

```console
$ manifestoo --addons-path /tmp/myaddons --select a tree
a (14.0.1.0.0)
├── b (14.0.1.0.0)
│   └── contacts (14.0+c)
│       └── mail (14.0+c)
│           ├── base_setup (14.0+c)
│           │   └── web (14.0+c)
│           ├── bus (14.0+c)
│           │   └── web ⬆
│           └── web_tour (14.0+c)
│               └── web ⬆
└── c (14.0.1.0.0)
    └── mail ⬆
```

To check that licenses are compatibles, use the `check-licenses` command:

```console
$ moo -d /tmp/myaddons check-licenses
a (GPL-3) depends on b (Other Proprietary)
```

And much more... See the documentation for more information.

<!--- quickstart-end -->


[github-ci]: https://github.com/sbidoul/manifestoo/actions/workflows/ci.yml/badge.svg
[github-link]: https://github.com/sbidoul/manifestoo
[codecov-badge]: https://codecov.io/gh/sbidoul/manifestoo/branch/master/graph/badge.svg
[codecov-link]: https://codecov.io/gh/sbidoul/manifestoo
[pypi-badge]: https://img.shields.io/pypi/v/manifestoo.svg
[pypi-link]: https://pypi.org/project/manifestoo
