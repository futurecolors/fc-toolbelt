# coding: utf-8
import os
from fabric.tasks import Task


class BaseWriterTask(Task):
    def get_template_path(self, filename):
        return os.path.join('fc_toolbelt/config_templates/', filename)

    def get_server_name(self, project, developer):
        return '%s.%s' % (project, developer)

    def get_socket_path(self, server_name):
        return '/tmp/%s.sock' % server_name
