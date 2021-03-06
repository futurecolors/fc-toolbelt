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
    * mysql access is required (.my.cnf)
    * all api tokens got to have sufficient permissions

Usage
-----
::

    fct COMMAND [command-specific-options]


Commands
^^^^^^^^

Use ``fct help COMMAND`` to see what options are available


:boilerplate:   Start new project from boilerplate, e.g. `tinned-django`_
:config:        Configure toolbelt for first usage
:git:           Useful git aliases, read more in fct help git
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


.. _docopt: http://docopt.org/
.. _tinned-django: https://github.com/futurecolors/tinned-django
