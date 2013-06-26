# coding: utf-8
from fabric.api import execute, run, settings, hide, puts
from fabric.tasks import Task


class BaseMysqlTask(Task):
    """ Base for all Mysql tasks with helpers"""

    def execute(self, sql, user):
        sql = sql.replace('"', r'\"')
        return run('echo "%s" | mysql --user="%s"' % (sql, user))


class CreateDevDb(Task):
    """ Create development mysql database for user """
    name = 'create_dev_db'

    def run(self, project, user, password=''):
        execute(CreateUser(), project, password)
        db_name = '%s_%s' % (project, user)
        execute(CreateDb(), db_name)
        execute(GrantPermissions(), db_name, user)

create_dev_db = CreateDevDb()


class CreateUser(BaseMysqlTask):
    name = 'create_user'
    MYSQL_USER_EXISTS = "SHOW GRANTS FOR '%s'@localhost;"
    MYSQL_CREATE_USER = "CREATE USER '%s'@'localhost' IDENTIFIED BY '%s';"

    def run(self, user, password):
        if self.user_exists(user):
            puts('User %s already exists' % user)
            return
        self.execute(self.MYSQL_CREATE_USER % (user, password), 'root')

    def user_exists(self, user):
        sql = self.MYSQL_USER_EXISTS % user
        with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
            result = self.execute(sql, 'root')
        return result.succeeded


class CreateDb(BaseMysqlTask):
    name = 'create_db'
    MYSQL_BASE_EXISTS = "USE %s;"
    MYSQL_CREATE_DB = """CREATE DATABASE %s
                                DEFAULT CHARACTER SET utf8
                                DEFAULT COLLATE utf8_general_ci;"""

    def run(self, name):
        if self.db_exists(name):
            puts('Database %s already exists' % name)
            return
        self.execute(self.MYSQL_CREATE_DB % name, 'root')

    def db_exists(self, name):
        with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
            result = self.execute(self.MYSQL_BASE_EXISTS % name, 'root')
        return result.succeeded


class GrantPermissions(BaseMysqlTask):
    name = 'grant_permissions'
    MYSQL_GRANT_PERMISSIONS = """GRANT ALL ON %s.* TO '%s'@'localhost';
                                 FLUSH PRIVILEGES;"""

    def run(self, name, user):
        self.execute(self.MYSQL_GRANT_PERMISSIONS % (name, user), 'root')
