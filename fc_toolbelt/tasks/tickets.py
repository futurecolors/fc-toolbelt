# coding: utf-8
from __future__ import print_function
import logging
from fabric.operations import local

from fabric.state import env
from fabric.utils import puts

from fc_toolbelt.tasks.redmine import GetIssues


logger = logging.getLogger('fc_toolbelt')


class DiffTickets(GetIssues):
    """ List of Redmine tickets urls, mentioned in commits that differ between two branches/tags.
    """
    name = 'tickets'
    GIT_CALL = """git log {from_ref} --not {to_ref} --format="%s" --no-merges | grep -E "#\d+" -o | uniq  | cut -c2- """

    def run(self, from_ref='origin/dev', to_ref='origin/master', **kwargs):

        ticket_ids = filter(None, self.git_ticket_ids(from_ref, to_ref))

        self.connect()
        puts('Querying Redmine...')
        if kwargs.get('by_ids'):
            issues = self.get_issues_by_ids(ticket_ids)
        else:
            issues = self.get_issues(**kwargs)

        logger.debug('%s: %s' % ('Redmine', [issue['id'] for issue in issues]))
        logger.debug('%s: %s' % ('Git', ticket_ids))

        get_issue_url = lambda issue_id: env.REDMINE_URL + '/issues/%s' % issue_id
        if kwargs.get('urls'):
            formatter = lambda issue: get_issue_url(issue['id'])
        elif kwargs.get('status'):
            formatter = lambda issue: u'#%s %s' % (issue['id'], issue['status']['name'])
        elif kwargs.get('full'):
            formatter = lambda issue: u'#{id} {status} {link} {subject}'.format(
                id=issue['id'],
                link=get_issue_url(issue['id']),
                status=issue['status']['name'],
                subject=issue['subject'],
            )
        else:
            formatter = lambda issue: u'#%s %s' % (issue['id'], issue['subject'])

        issues_urls = [formatter(issue) for issue in issues if str(issue['id']) in ticket_ids]
        map(print, issues_urls)

    def git_ticket_ids(self, from_ref, to_ref):
        """ List of ids"""
        git_log_output = local(self.GIT_CALL.format(from_ref=from_ref, to_ref=to_ref), capture=True)
        return git_log_output.split('\n')


diff_tickets = DiffTickets()
