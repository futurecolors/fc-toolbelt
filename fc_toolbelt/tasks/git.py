# coding: utf-8
from fabric.api import local, run
from fabric.tasks import Task


__all__ = ['prune']


class DeleteMergedBranches(Task):
    """Useful git aliases"""
    name = 'git'
    default_branches = ('dev', 'master')

    delete_merged_brances_cmd = ('echo git push origin'
                                 '$(git branch -r --merged origin/master'
                                 '| sed "s/origin\\//:/" | egrep -v "HEAD|%s")' % '|'.join(default_branches))

    def run(self):
        result = local(self.delete_merged_brances_cmd, capture=True)
        if result == 'git push origin':
            print "No old branches, yeah!"
        else:
            print result


prune = DeleteMergedBranches()
