# coding: utf-8
"""Future Colors Toolbelt

Starting new Django project should be dead simple.
A set of useful scripts to setup local development environment.

usage:
    fct <command> [options] [<args>...]
    fct [--version]
    fct [--help]

available commands:
    boilerplate  Start new project from boilerplate
    config       Configure toolbelt for first usage
    gitlab       Shortcuts to create projects & assign users
    help         Prints instruction how to use specific command
    jenkins      Create new jenkins jobs
    join         Create dev instance for new project member
    redmine      Create project, assign developers
    tickets      Tickets, mentioned in commits between two branches/tags
    update       Updates code, packages and reloads server

options:
  -h --help     Show this screen
  --version     Show version
  --verbose     Show debug information
  --force       Force
  --uwsgi-config=<config>
  --from=<from_ref>      Base branch/tag to diff from [default: origin/dev]
  --to=<to_ref>          Final branch/tag to diff to [default: origin/master]
  --query_id=<query_id>  Redmine query to filter tickets against
  --target_id=<target_id>

See 'fct help <command>' for more information on a specific command.
"""
import logging
import sys
import textwrap

from docopt import docopt
from fabric import state
from fabric.main import load_settings
from fabric.tasks import execute

import fc_toolbelt
from fc_toolbelt.tasks import django, setup
from fc_toolbelt.tasks.gitlab import create_repo, assign
from fc_toolbelt.tasks.jenkins import create_job
from fc_toolbelt.tasks.project import open_tin, add_developer
from fc_toolbelt.tasks.redmine import create_project, assign_permissions
from fc_toolbelt.tasks.tickets import diff_tickets


logger = logging.getLogger('fc_toolbelt')


def main():
    # Let's print help be default
    options = docopt(__doc__, argv=sys.argv[1:] if len(sys.argv) > 1 else ['--help'],
                     version=fc_toolbelt.__VERSION__)

    available_commands = ['boilerplate', 'config', 'gitlab', 'jenkins', 'join',
                          'redmine', 'tickets', 'update']
    command = options['<command>']

    # Load fabric defaults from ~/.fabricrc
    state.env.update(load_settings(state._rc_path()))

    if options['--verbose']:
        level = logging.DEBUG if options['--verbose'] else logging.INFO
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(level)
    else:
        state.output['commands'] = False
        state.env.output_prefix = False

    if options['<command>'] in available_commands:
        subcommand = globals()[command]
        options = docopt(subcommand.__doc__, argv=sys.argv[1:])
        exit(subcommand(options))
    elif options['<command>'] == 'help':
        if not options['<args>']:
            exit(__doc__)
        help_command = options['<args>'][0]
        if help_command in available_commands:
            exit(textwrap.dedent(globals()[help_command].__doc__))

    exit("%r is not a fct command. See 'fct --help'." % command)


def update(options):
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


def gitlab(options):
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
    if options['create_repo']:
        execute(create_repo, project_slug=options['<project_slug>'])
    elif options['assign']:
        execute(assign, project_slug=options['<project_slug>'], user_email=options['<user_email>'])


def jenkins(options):
    """
       Shortcuts to create jobs in jenkins.

       Template job is copied and templated ({{project}} is replaced with project slug).
       It's enabled after that and executed.

       Usage:
          fct jenkins create_job <project_slug> <job_name> [<template_job>]
    """
    if options['create_job']:
        execute(create_job,
                job_name=options['<job_name>'],
                project_slug=options['<project_slug>'],
                template_job=options['<template_job>'])


def config(options):
    """
        It will iterate every option in .fabricrc.tmpl prompting you
        to override default values and will write your version of .fabricrc

        Most of tasks require some sort of credentials to run.
        E.g. redmine tasks need API key, gitlab tasks need token and so on.
        You can provide these values each time you run a specific task,
        but it's too tedious. Best way is to store your credentials in
        .fabricrc file which mimics .bashrc

        Example .fabricrc (it's usually located in your $HOMEDIR)

            KEY1 = value
            KEY2 = another_value

        Usage:
            fct config [options]

        Options:
            -f --force     Ignore existing setup of toolbelt and reconfigure.
    """
    execute(setup.config, force=options.get('--force', False))


def redmine(options):
    """
       Shortcuts to create projects and assign developers in Redmine.

       Usage:
          fct redmine create_project <project_slug> [<project_name>]
          fct redmine assign <project_slug> <user_email>
    """
    if options['create_project']:
        execute(create_project,
                project_slug=options['<project_slug>'],
                project_name=options.get('<project_name>', None))
    elif options['assign']:
        execute(assign_permissions,
                project_slug=options['<project_slug>'],
                user_email=options['<user_email>'])


def tickets(options):
    """
       List of Redmine tickets urls, mentioned in commits that differ between two branches/tags.

       It's possible to filter specific tickets providing query_id and project_slug.
       If you specify ticket numbers in your commit messages (it's a best practice),
       like that:

           Refactored user registration
           Major speedups, added more tests. Fixes #16

       Redmine will show a link to your commit on ticket page and you can later
       track what commits are connected to specific task.

       Usage:
          fct tickets [options] <project_slug>

       Example:
          fct tickets futurecolors --from=origin/dev --to=origin/master  --query_id=42

       Options:
          --from=<from_ref>         Base branch/tag to diff from [default: origin/dev]
          --to=<to_ref>             Final branch/tag to diff to [default: origin/master]
          --query_id=<query_id>     Redmine query to filter tickets against (doesn't combine with version_id)
          --target_id=<target_id>  Redmine version id (doesn't combine with query_id)
          --verbose                 Show debug information
    """
    kwargs = {
        'project_id': options['<project_slug>'],
    }
    mapping = {
        '--from': 'from_ref',
        '--to': 'to_ref',
        '--query_id': 'query_id',
        '--target_id': 'fixed_version_id'
    }
    for arg in mapping.keys():
        if options.get(arg):
            kwargs[mapping[arg]] = options.get(arg)

    execute(diff_tickets, **kwargs)


def join(options):
    """
       Create dev instance for new project member

       * deploys code from gitlab repo on dev server
       * configures webserver for local development (ngnix+uwsgi)
       * sets up database <project>_<developer>

       Usage:
          fct join [options] <project_slug> <developer>

       Options:
          --verbose                  Show debug information
          --uwsgi-config=<config>    Change default uwsgi template
    """
    if options['join']:
        if options.get('--uwsgi-config'):
            state.env.UWSGI_CONFIG_TEMPLATE = options.get('--uwsgi-config')
        execute(add_developer, project_slug=options['<project_slug>'],
                               developer=options['<developer>'])


def boilerplate(options):
    """
       Start new project from boilerplate

       * creates new django project from template
       * pushes the code into gitlab repo

       Usage:
          fct boilerplate <project_slug>
    """
    if options['boilerplate']:
        execute(open_tin, project_slug=options['<project_slug>'])
