# coding: utf-8
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
        self.connect()
        puts('Querying Redmine...')
        issues = self.get_issues(**kwargs)
        ticket_ids = self.git_ticket_ids(from_ref, to_ref)
        logger.debug('%s: %s' % ('Redmine', [issue['id'] for issue in issues]))
        logger.debug('%s: %s' % ('Git', ticket_ids))
        get_issue_url = lambda issue_id: env.REDMINE_URL + '/issues/%s' % issue_id
        issues_urls = [get_issue_url(issue['id']) for issue in issues
                       if str(issue['id']) in ticket_ids]
        map(puts, issues_urls)

    def git_ticket_ids(self, from_ref, to_ref):
        """ List of ids"""
        git_log_output = local(self.GIT_CALL.format(from_ref=from_ref, to_ref=to_ref), capture=True)
        return git_log_output.split('\n')


diff_tickets = DiffTickets()
