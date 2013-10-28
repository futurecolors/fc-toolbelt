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


class GetBranch(Task):
    """Get branch by mask"""

    name = 'get_git_branch'
    get_branch_commnad = (
        """git for-each-ref --sort=committerdate --format="%(refname:short)" """
        """| grep "{0}" | tail -n 1"""
    )

    def run(self, git_branch, **kwargs):
        result = local(self.get_branch_commnad.format(git_branch), capture=True)

        branch_name = result.strip()

        if not branch_name:
            raise AttributeError(
                "Bad git branch mask: \n"
                "%s" % result
            )

        return branch_name


get_branch = GetBranch()
prune = DeleteMergedBranches()
