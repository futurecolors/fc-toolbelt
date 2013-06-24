# coding: utf-8
"""Future Colors Toolbelt

Starting new Django project should be dead simple.
A set of useful scripts to setup local development environment.

usage:
    fct <command> [<args>...]

available commands:
    help       Prints instruction how to use specific command
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
from fc_toolbelt.tasks.django import update


def main():
    # Let's print help be default
    args = docopt(__doc__, argv=sys.argv[1:] if len(sys.argv) > 1 else ['--help'],
                  version=fc_toolbelt.__VERSION__)

    available_commands = {
        'update': update
    }

    if args['<command>'] in available_commands.keys():
        execute(available_commands[args['<command>']])
    elif args['<command>'] == 'help':
        if not args['<args>']:
            exit(__doc__)
        command = args['<args>'][0]
        if command in available_commands.keys():
            exit(textwrap.dedent(available_commands[command].__doc__))

    exit("%r is not a fct command. See 'fct --help'." % args['<command>'])
