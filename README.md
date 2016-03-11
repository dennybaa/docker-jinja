# docker-jinja - dj

Extend your dockerfiles with Jinja2 syntax and logic.

Create new filter and functions for Jinja with simple datasource files.

Build status: [![Build Status](https://travis-ci.org/Grokzen/docker-jinja.svg?branch=master)](https://travis-ci.org/Grokzen/docker-jinja) [![Coverage Status](https://coveralls.io/repos/Grokzen/docker-jinja/badge.png)](https://coveralls.io/r/Grokzen/docker-jinja)


## Quickstart guide

### Installation and usage

Clone this repo. Navigate to root of repo. Run `pip install .` to install. All runtime python dependencies can be found in `requirements.txt`.
To install all development dependencies run `pip install -r dev-requirements.txt`.


Create a Dockerfile.jinja that contains all regular Dockerfile build steps and the jinja syntax. Run the following `dj` command:

```
dj -d Dockerfile.jinja -o Dockerfile -e OS=ubuntu:12.04 -s test-datasource.py -c conf.yaml
```

## CLI Options

    Usage:
      dj -d DOCKERFILE -o OUTFILE [-s DSFILE]... [-e ENV]... [-c CONFIGFILE]...
         [-v ...] [-q] [-h] [--version]

    Options:
      -c CONFIGFILE --config CONFIGFILE       file containing data config for dj (yaml or json format)
      -s DSFILE --datasource DSFILE           file that should be loaded as a datasource
      -d DOCKERFILE --dockerfile DOCKERFILE   dockerfile to render
      -e ENV --env ENV                        variable with form "key=value" that should be used in the rendering
      -o OUTFILE --outfile OUTFILE            output result to file
      -h --help                               show this help
      -v --verbosity                          verbosity level of logging messages. ( -v == CRITICAL )  ( -vvvvv == DEBUG )
      -V --version                            display the version number and exit
      -q --quiet                              silence all logging output no matter what




### Datasources

If you want to extend the Jinja syntax with additional filters and global functions you have the datasource pattern to help you (datasource file is a python script). You can use **-s/--datasource** to specify which data source files to load. Also you should be able to set datasources path list in any config files and `dj` will pick them up too.

Adding a python file to contrib folder and it will auto load during execution. Global and filter functions inside a datasource file should start with *_global_* and *_filter_* respectively to mark them so that they can be loaded into YAML environment.


### Global functions

A global function is a regular python function that you can call from jinja. These functions can be used to perform any useful task you require.

For example if you have the following code:

```python
def _global_foo():
    return "bar"
```

For instance this function used in a Dockerfile:

```
RUN echo '{{ foo() }}'
```
 will be rendered to `RUN echo 'bar'`.

### Filter functions

To create a new filter function you define a method within a datasource then follow by the name you want to use in your Dockerfile.

For example if you have the following code

```python
def _filter_bar(arg):
    return arg.upper()
```

You can call it from jinja, for example like this:

```Shell
RUN echo '{{ "opa"|bar }}'
```

This will be rendered  to `RUN echo 'OPA'`.


## Default configuration files

It is possible to create predefined configuration files with settings, environment variables and data sources.

`dj` tries to load the following default configuration files in the following order:

- ~/.dj.yaml
- ~/.dj.json
- $CWD + '.dj.yaml'
- $CWD + '.dj.json'

YAML is the file format to prefer but json is also supported.


# Supported python version

- 2.7
- 3.3
- 3.4

Python 3.2 will not be supported because Jinja2 is only supported on python >= 3.3 (Reference: http://jinja.pocoo.org/docs/intro/). If other rendering engines would be supported then python 3.2 can be supported for those engines.
Python 2.6 will not be supported.


# Contribute

Open an Issue on github describing the problem you have.

If you have a fix for the problem or want to add something to contrib library, open a PR with your fix. The PR must contain some test to verify that it work if it is a bug fix or new feature.  All tests in all supported python environments must pass on TravisCI before a PR will be accepted.


# License

See LICENSE file. (MIT)
