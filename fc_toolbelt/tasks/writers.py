# coding: utf-8
import os
import socket
from functools import partial
from fabric.context_managers import cd, settings, show
from fabric.contrib.files import upload_template

from fabric.operations import sudo, run
from fabric.state import env
from fabric.tasks import Task
from fabric.utils import puts


class BaseWriterTask(Task):
    def get_template_path(self, template_file=None):
        base_path = 'fc_toolbelt/config_templates/'
        if file:
            return os.path.join(base_path, template_file)
        else:
            return base_path

    def get_server_name(self, project, developer):
        return '%s.%s' % (project, developer)

    def get_socket_path(self, server_name):
        return '/var/run/uwsgi/%s.sock' % server_name

    def get_project_path(self, project, developer):
        return os.path.join(env.PROJECTS_PATH_TEMPLATE % ({'user': developer}), project)

    def get_env_path(self, project, developer):
        return os.path.join(env.ENVS_PATH_TEMPLATE % ({'user': developer}), project)


class WriteProjectFolders(BaseWriterTask):
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

    def copy_repo_files_install_env(self, project_slug, project_path, repo_url):
        """ workaround not having permissions in target dir to clone directly"""
        tmp_dir = '/tmp/fctools/%s' % project_slug
        sudo('rm -rf %s' % tmp_dir)
        with settings(show('commands'), warn_only=True):  # so that you can enter credentials
            run('git clone %s %s -b dev' % (repo_url, tmp_dir))  # dev branch is default
        sudo('rm -rf %s/.git' % tmp_dir)
        sudo('cp -R %s/* %s' % (tmp_dir, project_path))
        sudo('rm -rf %s' % tmp_dir)

    def run(self, project_slug, developer, repo_url=None):
        self.user_sudo = user_sudo = partial(sudo, user=developer)
        project_path = self.get_project_path(project_slug, developer)
        with cd(project_path):
            user_sudo('mkdir -p %s' % project_slug)
        if repo_url:
            self.copy_repo_files_install_env(project_slug, project_path, repo_url)
        mkenv_command = 'mkvirtualenv --python=python2.7 -a %(project_path)s -r %(reqs)s %(env_name)s'
        user_sudo(mkenv_command % {'project_path': self.get_project_path(project_slug, developer),
                                   'reqs': 'requirements.txt',
                                   'env_name': project_slug})
        with cd(env.ENVS_PATH_TEMPLATE % {'user': developer}):
            user_sudo('touch %s/reload.txt' % project_slug)
        with cd(env.PROJECTS_PATH_TEMPLATE % ({'user': developer})):
            self.run_chmod(project_slug, developer)

write_project = WriteProjectFolders()


class WriteUwsgiConfig(BaseWriterTask):
    """ Write uwsgi config for project+developer"""
    name = 'write_uwsgi'

    def get_context(self, project_slug, developer):
        server_name = self.get_server_name(project_slug, developer)
        project_dir = self.get_project_path(project_slug, developer)
        env_dir = self.get_env_path(project_slug, developer)
        return {
            'PATH_TO_VIRTUALENV': env_dir,
            'PROJECT_PATH': project_dir,
            'SERVER_NAME': server_name,
            'USER': developer,
            'PROJECT_NAME': project_slug,
        }

    def run(self, project_slug, developer):
        config_name = self.get_server_name(project_slug, developer)
        config_available_path = '/etc/uwsgi/apps-available/%s.ini' % config_name
        config_enabled_path = '/etc/uwsgi/apps-enabled-2.7/%s.ini' % config_name

        upload_template(
            template_dir=self.get_template_path(),
            filename='uwsgi.config.tmpl',
            destination=config_available_path,
            context=self.get_context(project_slug, developer),
            use_sudo=True,
            use_jinja=True,
            backup=False
        )
        sudo('ln -fs %(available)s %(enabled)s' % {
            'available': config_available_path,
            'enabled': config_enabled_path
        })

write_uwsgi = WriteUwsgiConfig()


class WriteNginxConfig(BaseWriterTask):
    """ Write nginx config for project+developer and reload nginx"""
    name = 'write_nginx'

    def get_context(self, project_slug, developer):
        server_name = self.get_server_name(project_slug, developer)
        return {
            'SERVER_NAME': server_name,
            'SERVER_IP': socket.gethostbyname(env.hosts),
            'SOCKET_PATH': self.get_socket_path(server_name),
            'PROJECT_PATH': self.get_project_path(project_slug, developer),
        }

    def run(self, project_slug, developer, noreload=False):
        context = self.get_context(project_slug, developer)
        upload_template(
            template_dir=self.get_template_path(),
            filename='nginx.config.tmpl',
            destination='/etc/nginx/fc/%s' % self.get_server_name(project_slug, developer),
            context=context,
            use_jinja=True,
            use_sudo=True,
            backup=False
        )
        if not noreload:
            sudo('/etc/init.d/nginx reload')
        puts('Add this lines to your /etc/hosts:')
        puts('%(ip)s   %(project_domain)s' % {'ip': context['SERVER_IP'], 'project_domain': context['SERVER_NAME']})
        puts('%(ip)s   *.%(project_domain)s.fcdev.ru' % {'ip': context['SERVER_IP'], 'project_domain': context['SERVER_NAME']})

write_nginx = WriteNginxConfig()
