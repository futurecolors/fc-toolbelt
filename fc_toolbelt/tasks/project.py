# coding: utf-8
import os
from functools import partial
from fabric.colors import green

from fabric.context_managers import cd, prefix
from fabric.operations import run, sudo
from fabric.state import env
from fabric.tasks import Task, execute
from fabric.utils import puts
from fc_toolbelt.tasks.gitlab import BaseGitlabTask
from fc_toolbelt.tasks.mysql import create_dev_db

from .writers import write_uwsgi, write_nginx, write_project


class OpenTin(BaseGitlabTask):
    """ Commit new Django project from template into repo"""

    def run(self, project_slug):
        self.project_slug = project_slug
        tmpdir = '/tmp/fctools/'
        run('rm -rf /tmp/fctools/')
        run('mkdir -p %s' % tmpdir)

        self.create_folders_from_can(tmpdir)
        self.connect()
        repo_url = self.get_repo_url_by_path(project_slug)
        self.make_initial_commit(os.path.join(tmpdir, self.project_slug), repo_url)
        run('rm -rf /tmp/fctools/')

    def create_folders_from_can(self, dir):
        """ Clone project template, make virtualenv, custom startproject"""
        with cd(dir):
            env_name = 'canned_env'
            template_project_dirname = 'project_template'
            run('git clone %(repo)s %(dir)s' % {'repo': env.TEMPLATE_PROJECT_REPO,
                                                'dir': template_project_dirname})
            run('virtualenv %s' % env_name)
            with prefix('source %s/bin/activate' % env_name):
                run('pip install django')
                run('django-admin.py startproject %(project)s --template=%(template)s --extension=py,gitignore' % {
                    'project': self.project_slug,
                    'template': os.path.join(template_project_dirname, env.TEMPLATE_PROJECT_PACKAGE),
                })

    def make_initial_commit(self, project_dir, repo_url):
        """ Init git repo and push it as current user """
        with cd(project_dir):
            run('git init')
            run('git config user.email "%s@fctools"' % env.user)
            run('git config user.name "%s"' % env.user)
            run('git add .')
            run('git commit -m "Initial commit via fctools"')
            run('git remote add origin %s' % repo_url)
            run('git checkout -b dev')
            run('git push --all --force')

open_tin = OpenTin()


class AddDeveloper(BaseGitlabTask):
    """ Creates development project environment for developer"""
    name = 'add_developer'

    def run(self, project_slug, developer, uwsgi_config=None):
        self.project_slug = project_slug
        self.developer = developer
        self.connect()
        repo_url = self.get_repo_url_by_path(project_slug)
        self.setup_files(repo_url)
        self.setup_databases()
        self.setup_http()
        puts(green('Congrats! Now visit: %s' % ('http://%s.%s' % (project_slug, developer))))

    def setup_files(self, repo_url):
        sudo_user = partial(sudo, user=self.developer)
        sudo_user('mkdir -p %s' % env.PROJECTS_PATH_TEMPLATE % {'user': self.developer})
        puts('Setting up new project "%s" for %s' % (self.project_slug, self.developer))
        execute(write_project, project_slug=self.project_slug,
                               developer=self.developer,
                               repo_url=repo_url)
        puts('Created project "%s" layout for %s' % (self.project_slug, self.developer))

    def setup_databases(self):
        execute(create_dev_db, self.project_slug, self.developer)
        puts('Setup of dev db "%s" for %s is finished' % (self.project_slug, self.developer))

    def setup_http(self):
        execute(write_uwsgi, self.project_slug, self.developer)
        execute(write_nginx, self.project_slug, self.developer)
        puts('Nginx+uwsgi are set up for "%s" project, developer %s' % (self.project_slug, self.developer))

add_developer = AddDeveloper()
