# coding: utf-8
"""Future Colors Toolbelt

Starting new Django project should be dead simple.
A set of useful scripts to setup local development environment.

usage:
    fct <command> [<args>...]

available commands:
    help       Prints instruction how to use specific command
    gitlab     Shortcuts to create projects & assign users
    jenkins    Create new jenkins jobs
    update     Updates code, packages and reloads server

options:
  -h --help     Show this screen.
  --version     Show version.

See 'fct help <command>' for more information on a specific command.
"""
import sys
import textwrap

from docopt import docopt
from fabric.tasks import execute

import fc_toolbelt
from fc_toolbelt.tasks import django
from fc_toolbelt.tasks.gitlab import create_repo, assign
from fc_toolbelt.tasks.jenkins import create_job


def main():
    # Let's print help be default
    options = docopt(__doc__, argv=sys.argv[1:] if len(sys.argv) > 1 else ['--help'],
                     version=fc_toolbelt.__VERSION__)

    available_commands = ['gitlab', 'jenkins', 'update']
    command = options['<command>']

    if options['<command>'] in available_commands:
        globals()[command](sys.argv)
    elif options['<command>'] == 'help':
        if not options['<args>']:
            exit(__doc__)
        help_command = options['<args>'][0]
        if help_command in available_commands:
            exit(textwrap.dedent(globals()[help_command].__doc__))

    exit("%r is not a fct command. See 'fct --help'." % command)


def update(*args):
    """
       Update code, install packages, sync/migrate and reload.

       Usage:
           fct update

       * update current git repo (pull)
       * install latest packages fro requirements.txt
       * update database (syncdb & migrate)
       * reload uwsgi instance
    """
    execute(django.update)


def gitlab(argv):
    """
       Shortcuts to create projects & assign users.

       Creating repo
         Creates repo by name, does not assign any teams.
       Assign members
         Assigns 1 member to project with default developer role.

       Usage:
          fct gitlab create_repo <project_slug>
          fct gitlab assign <project_slug> <user_email>
    """
    options = docopt(gitlab.__doc__, argv=argv[1:] if len(argv) > 1 else ['--help'])
    if options['create_repo']:
        execute(create_repo, project_slug=options['<project_slug>'])
    elif options['assign']:
        execute(assign, project_slug=options['<project_slug>'], user_email=options['<user_email>'])


def jenkins(argv):
    """
       Shortcuts to create jobs in jenkins.

       Template job is copied and templated ({{project}} is replaced with project slug).
       It's enabled after that and executed.

       Usage:
          fct jenkins create_job <project_slug> <job_name> [<template_job>]
    """
    options = docopt(jenkins.__doc__, argv=argv[1:] if len(argv) > 1 else ['--help'])
    if options['create_job']:
        execute(create_job,
                job_name=options['<job_name>'],
                project_slug=options['<project_slug>'],
                template_job=options['<template_job>'])
