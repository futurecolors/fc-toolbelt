# coding: utf-8
import os
from functools import partial
from fabric.context_managers import cd

from fabric.operations import sudo, run
from fabric.state import env
from fabric.tasks import Task

from .utils import inside_projects


class BaseWriterTask(Task):
    def get_template_path(self, filename):
        return os.path.join('fc_toolbelt/config_templates/', filename)

    def get_server_name(self, project, developer):
        return '%s.%s' % (project, developer)

    def get_socket_path(self, server_name):
        return '/tmp/%s.sock' % server_name


class WriteProjectFolders(Task):
    """ Local deploy to dev server per developer

        * create project folder
        * create virtualenv
        * install python packages
    """
    name = 'write_project'

    def run_chmod(self, project_slug, developer):
        sudo('chown -R {user}:{group} {project}'.format(
            user=developer,
            group=env.DEVELOPERS_USERGROUP,
            project=project_slug)
        )
        sudo('chmod -R 755 {project}'.format(user=developer, project=project_slug))

    def copy_repo_files_install_env(self, project_slug, repo_url):
        """ workaround not having permissions in target dir to clone directly"""
        tmp_dir = '/tmp/fctools/%s' % project_slug
        run('rm -r %s' % tmp_dir)
        run('git clone %s %s -b dev' % (repo_url, tmp_dir))  # dev branch is default
        run('rm -r %s/.git' % tmp_dir)
        self.user_sudo('cp -R %s/* src' % tmp_dir)
        self.user_sudo('env/bin/pip install -r src/requirements.txt --download-cache=/tmp/fctools-cache/')
        run('rm -r %s' % tmp_dir)

    @inside_projects
    def run(self, project_slug, developer, repo_url=None):
        self.user_sudo = user_sudo = partial(sudo, user=developer)
        user_sudo('mkdir -p %s' % project_slug)
        user_sudo('mkvirtualenv --python=python2.7 %s' % project_slug)
        if repo_url:
            with cd(project_slug):
                self.copy_repo_files_install_env(project_slug, repo_url)
        with cd(env.ENVS_PATH_TEMPLATE % {'user': developer}):
            user_sudo('touch %s/reload.txt' % project_slug)
        self.run_chmod(project_slug, developer)

write_project = WriteProjectFolders()
