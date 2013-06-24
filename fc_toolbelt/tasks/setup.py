# coding: utf-8
import string
import os

from fabric.api import prompt, abort
from fabric.colors import yellow, red
from fabric.state import env
from fabric.utils import puts
import fc_toolbelt

from .writers import BaseWriterTask


class ConfigToolbelt(BaseWriterTask):
    """ Write default values to .fabricrc
    """
    name = 'config'

    fabricrc_path = os.path.expanduser('~/.fabricrc')
    installation_marker = 'PROJECTS_PATH_TEMPLATE'

    def check_toolbelt_is_configured(self):
        if not os.path.exists(self.fabricrc_path):
            return False
        return self.installation_marker in open(self.fabricrc_path).read()

    def prompt_user(self):
        config = {}
        context = env
        for line in open(self.get_template_path('.fabricrc.tmpl')).readlines():
            comment = None
            if '#' in line:
                line, comment = line.split('#')
            key, default = map(string.strip, line.split('='))
            default = default.format(**context)
            config[key] = prompt(comment or key, default=default)
        return config

    def write_config(self, config):
        f = open(self.fabricrc_path, 'wa')
        f.writelines(['%s = %s\n' % (k, v) for k, v in config.iteritems()])
        f.close()

    def run(self, force=False):
        if force:
            puts(yellow('WARNING: your .fabricrc will be overwritten, stop this task if this is not what you wanted.'))
        else:
            is_configured = self.check_toolbelt_is_configured()
            if is_configured:
                puts(open(self.fabricrc_path).read())
                abort(red('FC Toolbelt %s is already configured in .fabricrc. '
                      'Run fct config --force to rewrite config.' % fc_toolbelt.__VERSION__))

        config = self.prompt_user()
        self.write_config(config)
        puts('Config successfully written, now you can use all of the commands')


config = ConfigToolbelt()
