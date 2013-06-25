# coding: utf-8
import json

from fabric.colors import red, yellow, green
from fabric.state import env
from fabric.tasks import Task
from fabric.utils import abort, puts
from hammock import Hammock
import requests


__all__ = ['create_project', 'assign_permissions']


class BaseRedmineTask(Task):
    """ Base class for all Redmine tasks

        You need to call BaseRedmineTask.connect in order to use api.
    """

    def connect(self, *args, **kwargs):
        REDMINE_URL = env.get('REDMINE_URL', '').strip('/')
        if not REDMINE_URL:
            abort(red('Provide REDMINE_URL pointing to your redmine instance'))

        REDMINE_API_KEY = env.get('REDMINE_API_KEY', '')
        if not REDMINE_API_KEY:
            abort(red('Go to %s/my/account and grab yourself a api key' % REDMINE_URL))

        self.api = Hammock(env.REDMINE_URL,
                           headers={'Content-Type': 'application/json',
                                    'X-Redmine-API-Key': env.REDMINE_API_KEY})


class CreateProject(BaseRedmineTask):
    """ Create new project """
    name = 'create_project'

    def run(self, project_slug, name=None):
        self.connect()
        response = self.api('projects.json').POST(data=json.dumps({
            'project': {
                'name': name or project_slug,
                'identifier': project_slug,
            }
        }))
        if response.status_code == requests.codes.unprocessable:
            puts(yellow('Project already exists'))

create_project = CreateProject()


class AssignPermissions(BaseRedmineTask):
    """ Add developers to project"""
    name = 'assign_permissions'

    def run(self, project_slug, user_email):
        """ Grant developer permission to user with specified email.
        """
        self.connect()
        developer_role_id = env.get('REDMINE_DEVELOPER_ROLE_ID', None)
        if not developer_role_id:
            abort(red('Please provide REDMINE_DEVELOPER_ROLE_ID setting'))
        user_id = self.get_user_id_by_email(user_email)
        response = self.api('projects/%s/memberships.json' % project_slug).POST(data=json.dumps({
            'membership': {
                'user_id': user_id,
                'role_ids': [developer_role_id]
            }
        }))
        if response.status_code == requests.codes.ok:
            puts('User %s added to project %s' % (user_email, project_slug))

    def get_user_id_by_email(self, user_email):
        response = self.api('users.json').GET()
        if response.status_code == 403:
            abort(red('Admin permissions required'))
        users = response.json['users']
        user = filter(lambda u: u['mail'] == user_email, users)
        if not user:
            abort(red('No user with email %s' % user_email))
        return user[0]['id']

assign_permissions = AssignPermissions()


class GetIssues(BaseRedmineTask):
    """ Get all issues, abstracting pagination"""

    def run(self, **kwargs):
        """ Example kwargs: project_id, query_id"""
        self.connect()
        return self.get_issues(**kwargs)

    def get_issues(self, **kwargs):
        """ Issue dicts """
        offset = 0
        limit = 100
        issues, total_count = self.get_issues_page(offset, limit, **kwargs)
        while offset + limit < total_count:
            offset += limit
            new_issues, total_count = self.get_issues_page(offset, **kwargs)
            issues += new_issues
        return issues

    def get_issues_page(self, offset=0, limit=100, **kwargs):
        params = {'limit': limit, 'offset': offset}
        params.update(kwargs)
        resp = self.api('issues.json').GET(params=params)
        return resp.json()['issues'], resp.json()['total_count']
