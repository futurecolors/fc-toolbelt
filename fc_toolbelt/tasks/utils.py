# coding: utf-8
from functools import wraps
from fabric.context_managers import cd
from fabric.state import env


def inside_projects(func):
    @wraps(func)
    def inner(self, *args, **kwargs):
        with cd(env.PROJECTS_PATH_TEMPLATE % {'user': kwargs['developer']}):
            return func(self, *args, **kwargs)
    return inner
