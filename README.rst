Future Colors Toolbelt
======================

Starting new Django project should be dead simple.
A set of useful scripts to setup local development environment.

Installation
------------
::

    pip install -e git+https://github.com/futurecolors/fc-toolbelt#egg=fc_toolbelt
    fct config

Make sure you have sufficient permissions:

    * sudo access is required
    * mysql access is required

Usage
-----
::

    fct COMMAND [command-specific-options]
    fct help COMMAND


Commands
^^^^^^^^

:boilerplate:   Start new project from boilerplate
:config:        Configure toolbelt for first usage
:gitlab:        Shortcuts to create repos & assign users
:help:          Usage instructions
:jenkins:       Create new jenkins jobs
:join:          Create dev instance for new project member
:redmine:       Create redmine project, assign developers
:tickets:       Tickets, mentioned in commits between two branches/tags
:update:        Updates code, packages and reloads server


Contributing
------------

Console client is based on `docopt`_ DSL, providing option parsing.

To add command: put it in readme, add it to ``cli.py`` docstring, create function
with same name in cli module and specify appropriate docstring for it.

Module-level docstring serves as fct help, function-level docstrings
serve as subcommands help and parser spec.
