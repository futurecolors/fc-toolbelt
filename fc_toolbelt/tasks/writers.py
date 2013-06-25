# coding: utf-8
import os
from functools import partial
import socket
from fabric.context_managers import cd
from fabric.contrib.files import upload_template

from fabric.operations import sudo, run
from fabric.state import env
from fabric.tasks import Task

from .utils import inside_projects


class BaseWriterTask(Task):
    def get_template_path(self):
        return 'fc_toolbelt/config_templates/'

    def get_server_name(self, project, developer):
        return '%s.%s' % (project, developer)

    def get_socket_path(self, server_name):
        return '/var/run/uwsgi/%s.sock' % server_name

    def get_project_path(self, project, developer):
        return os.path.join(env.PROJECTS_PATH_TEMPLATE % ({'user': developer}), project)


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


class WriteUwsgiConfig(BaseWriterTask):
    """ Write uwsgi config for project+developer"""
    name = 'write_uwsgi'

    def get_context(self, project_slug, developer):
        server_name = self.get_server_name(project_slug, developer)
        project_dir = self.get_project_path(project_slug, developer)
        env_dir = os.path.join(project_dir, 'env')
        return {
            'GROUP': env.DEVELOPERS_USERGROUP,
            'RELOAD_TXT': os.path.join(env_dir, 'reload.txt'),
            'PATH_TO_VIRTUALENV': env_dir,
            'PROJECT_PATH': project_dir,
            'SERVER_NAME': server_name,
            'SOCKET_PATH': self.get_socket_path(server_name),
            'USER': developer,
            'PROJECT_NAME': project_slug,
        }

    def run(self, project_slug, developer):
        config_name = self.get_server_name(project_slug, developer)
        config_available_path = '/etc/uwsgi/apps-available/%s.xml' % config_name
        config_enabled_path = '/etc/uwsgi/apps-enabled-2.7/%s.xml' % config_name

        upload_template(
            template_dir=self.get_template_path(),
            filename='uwsgi.config.tmpl',
            destination=config_available_path,
            context=self.get_context(project_slug, developer),
            use_sudo=True,
            use_jinja=True,
            backup=False
        )
        sudo('ln -s %(available)s %(enabled)s' % {
            'available': config_available_path,
            'enabled': config_enabled_path
        })

write_uwsgi = WriteUwsgiConfig()


class WriteNginxConfig(BaseWriterTask):
    """ Write nginx config for project+developer"""
    name = 'write_nginx'

    def get_context(self, project_slug, developer):
        server_name = self.get_server_name(project_slug, developer)
        return {
            'SERVER_NAME': server_name,
            'SERVER_IP': socket.gethostbyname(env.hosts),
            'SOCKET_PATH': self.get_socket_path(server_name),
            'PROJECT_PATH': self.get_project_path(project_slug, developer),
        }

    def run(self, project_slug, developer):
        upload_template(
            template_dir=self.get_template_path(),
            filename='nginx.config.tmpl',
            destination='/etc/nginx/fc/%s' % self.get_server_name(project_slug, developer),
            context=self.get_context(project_slug, developer),
            use_jinja=True,
            use_sudo=True,
            backup=False
        )

write_nginx = WriteNginxConfig()
