# coding: utf-8
from fabric.context_managers import settings, hide
from fabric.tasks import Task
from fabric.api import local
from fabric.utils import puts


__all__ = ['update']


class BaseUpdateLocalEnvTask(Task):
    """Update local project environment """
    name = 'update'

    def update_code(self):
        puts('Updating code...')
        # In case it's not a git repo, skip
        with settings(hide('warnings'), warn_only=True):
            local('git pull')

    def virtualenv_update(self):
        """Update packages first"""
        puts('Installing packages...')
        local('pip install -r requirements.txt')

    def reload(self):
        """In case we're running in-non autoreload mode
           we need to restart server
        """
        puts('Reloading application...')
        local('touch ../reload.txt')


class DjangoUpdateLocalEnv(BaseUpdateLocalEnvTask):

    def smart_syncdb_migrate(self):
        """Workaround manage.py migrate complications
           * run syncdb in case it's our first run,
             so we make sure south_migrationhistory table is created
           * run migrate to apply latest migrations
           * run syncdb again to populate contrib.auth.models
        """
        local('python manage.py syncdb')
        local('python manage.py migrate')
        local('python manage.py syncdb --all')

    def run(self, *args, **kwargs):
        puts('Update process started...')
        self.update_code()
        self.virtualenv_update()
        self.smart_syncdb_migrate()
        self.reload()


update = DjangoUpdateLocalEnv()
