# coding: utf-8
from fabric.colors import red
from fabric.state import env
from fabric.tasks import Task
from fabric.utils import abort, puts
from jenkinsapi import jenkins


class BaseJenkinsTask(Task):
    """ Base for all Jenkins tasks

        Required env variables:
            * JENKINS_URL
            * JENKINS_LOGIN
            * JENKINS_PASSWORD
            * JENKINS_TEMPLATE_JOB
    """

    def run(self):
        self.JENKINS_URL = env.get('JENKINS_URL', '').strip('/')
        if not self.JENKINS_URL:
            abort(red('Provide env variable JENKINS_URL pointing to your jenkins instance'))

        JENKINS_LOGIN = env.get('JENKINS_LOGIN', '')
        JENKINS_PASSWORD = env.get('JENKINS_PASSWORD', '')
        if not all([JENKINS_LOGIN, JENKINS_PASSWORD]):
            abort(red('Provide both JENKINS_LOGIN and JENKINS_PASSWORD to connect to api'))

        self.api = jenkins.Jenkins(self.JENKINS_URL, JENKINS_LOGIN, JENKINS_PASSWORD)


class CreateJob(BaseJenkinsTask):
    """ Create new job in Jenkins from template job """
    name = 'create_job'

    def run(self, job_name, project_slug, template_job=None):
        super(CreateJob, self).run()
        template_job = template_job or env.get('JENKINS_TEMPLATE_JOB', 'example-tests')
        job = self.api.copy_job(template_job, job_name)
        job.enable()
        self.setup_job_config(job, context={'project': project_slug})
        job.invoke()
        puts("Created job %s/job/%s/" % (self.JENKINS_URL, job_name))

    def setup_job_config(self, job, context):
        config = job.get_config()
        config = config.format(**context)
        job.update_config(config)

create_job = CreateJob()
