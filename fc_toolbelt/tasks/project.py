# coding: utf-8
import os

from fabric.context_managers import cd, prefix
from fabric.operations import run
from fabric.state import env
from fabric.tasks import Task


class OpenTin(Task):
    """ Commit new Django project from template into repo"""

    def run(self, project_slug, repo_url):
        self.project_slug = project_slug
        tmpdir = '/tmp/fctools/'
        run('rm -rf /tmp/fctools/')
        run('mkdir -p %s' % tmpdir)

        self.create_folders_from_can(tmpdir)
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
