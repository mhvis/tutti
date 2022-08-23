import logging
from argparse import ArgumentParser

from django.core.management import BaseCommand
from ldap3.utils.log import set_library_log_detail_level, BASIC

from members.models import Instrument, ExternalCard, Key, QGroup, Person, GroupMembership, ExternalCardLoan
from sync.clone import CLONE_SEARCH, clone, check_for_issues
from sync.ldap import get_ldap_entries, get_connection


class Command(BaseCommand):
    help = 'Clones the full LDAP database and updates the ID attribute on LDAP.'

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('--debug',
                            action='store_true',
                            help='Enable ldap3 debug output.')

    def handle(self, *args, **options):
        if options['debug']:
            logging.basicConfig(level=logging.DEBUG)
            set_library_log_detail_level(BASIC)

        with get_connection() as conn:
            # First fetch LDAP data and check for issues
            self.stdout.write('Fetching entries from LDAP...')
            stuff = get_ldap_entries(conn, CLONE_SEARCH)
            self.stdout.write('Fetched {} entries'.format(len(stuff)))

            issues = check_for_issues(stuff)
            if issues:
                self.stdout.write('Found issues with the LDAP data:')
                for issue in issues:
                    self.stdout.write('* {}'.format(issue))
                return

            # Store data
            self.stdout.write('Found no data issues')
            y = input('Proceed with storing the data? All current Django entries will be removed! [y/N] ')
            if y != 'y':
                self.stdout.write('Cancelled')
                return

            self.stdout.write('Deleting Django entries...')
            GroupMembership.objects.all().delete()
            ExternalCardLoan.objects.all().delete()
            Instrument.objects.all().delete()
            QGroup.objects.all().delete()
            Person.objects.all().delete()
            ExternalCard.objects.all().delete()
            Key.objects.all().delete()

            self.stdout.write('Saving entries to database...')
            link_updates = clone(stuff)

            self.stdout.write('Entries created, need to do the following link attribute updates:')
            for update in link_updates:
                self.stdout.write('* {}'.format(update))

            y = input('Apply LDAP operations? [y/N] ')
            if y != 'y':
                self.stdout.write('Cancelled')
                return

            self.stdout.write('Updating link attribute on the LDAP database...')
            for update in link_updates:
                update.apply(conn)

            self.stdout.write('Cloning finished')
