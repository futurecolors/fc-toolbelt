# coding: utf-8
import urlparse

from fabric.api import env
from fabric.colors import red, yellow
from fabric.tasks import Task
from fabric.utils import abort, puts
from hammock import Hammock
import requests


class BaseGitlabTask(Task):
    """ Base for all Gitlab tasks

        You need to call super().connect in every subclass in order to use api.

        Required env variables:
            * GITLAB_URL
            * GITLAB_TOKEN

        Exmaple: export GITLAB_URL=http://gilabhq.com/
                 export GITLAB_TOKEN=2334859fa3458903
    """
    def project_exists(self, project_slug):
        return project_slug in [project['code'] for project in self.api.projects.GET().json]

    def get_user_by_email(self, email):
        return filter(lambda user: user['email'] == email, self.api.users.GET().json)[0]

    def get_users_emails(self):
        return [user['email'] for user in self.api.users.GET().json if not user['blocked']]

    def connect(self):
        self.GITLAB_URL = env.get('GITLAB_URL', '').strip('/')
        if not self.GITLAB_URL:
            abort(red('Provide env variable GITLAB_URL pointing to your Gitlab instance'))

        self.GITLAB_HOST = urlparse.urlparse(self.GITLAB_URL).netloc

        GITLAB_TOKEN = env.get('GITLAB_TOKEN', '')
        if not GITLAB_TOKEN:
            abort(red('Go to %s/profile/account and grab yourself a token' % self.GITLAB_URL))

        self.api = Hammock(self.GITLAB_URL, params={'private_token': env.GITLAB_TOKEN}).api('v2')
        return self


class CreateRepo(BaseGitlabTask):
    """ Create new repository via Gitlab """
    name = 'create_repo'

    def run(self, project_slug):
        super(CreateRepo, self).connect()
        response = self.api.projects.POST(params={'name': project_slug})
        if response.status_code != requests.codes.created:
            abort('Project not created %s' % response.content)
        puts("Created repository %s/%s" % (self.GITLAB_URL, project_slug))
        repo_url = "git@%(host)s:%(path)s.git" % {'host': self.GITLAB_HOST,
                                                  'path': response.json['path']}
        return repo_url

create_repo = CreateRepo()


class AssignDeveloper(BaseGitlabTask):
    """ Add developers to project via Gitlab

        Current limitation: you can only manipulate projects you have rights to.
        Can be avoided using a master token (TBD)
    """
    name = 'assign'
    DEVELOPER = 30
    MASTER = 40
    REPORTER = 20
    GUEST = 10

    def run(self, project_slug, user_email, access_level=DEVELOPER):
        puts('Creating project "%r"...' % project_slug)
        super(AssignDeveloper, self).connect()
        if not (self.project_exists(project_slug)):
            abort(red("Project %s does not exist or you don't have right to manipulate its members" % project_slug))

        try:
            user = self.get_user_by_email(user_email)
        except IndexError:
            abort(red('No user with email %s registered at Gitlab' % user_email))
            return

        response = self.api.projects(project_slug).members.POST(data={
            'id': project_slug,
            'user_id': user['id'],
            'access_level': access_level})

        if response.status_code != requests.codes.created:
            puts(yellow('User %s not added %s (might be already added)' % (user_email, response.content)))
        else:
            puts("Assigned %s to project %s" % (user['name'], project_slug))

assign = AssignDeveloper()
