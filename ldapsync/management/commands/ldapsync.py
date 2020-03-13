import logging
from argparse import ArgumentParser

from django.core.management import BaseCommand
from ldap3.utils.log import set_library_log_detail_level, BASIC

from ldapsync.ldap import get_connection, get_ldap_entries
from ldapsync.models import LDAPPerson, LDAPGroup, get_local_entries
from ldapsync.sync import sync


class Command(BaseCommand):
    help = 'One-way sync local database to remote LDAP database. Only modifies LDAP database.'

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('-y',
                            action='store_true',
                            help='Directly apply sync without asking for confirmation.')
        parser.add_argument('--debug',
                            action='store_true',
                            help='Enable ldap3 debug output.')

    def handle(self, *args, **options):
        if options['debug']:
            logging.basicConfig(level=logging.DEBUG)
            set_library_log_detail_level(BASIC)

        self.stdout.write('Retrieving entries from local database...')
        local_entries = get_local_entries()

        with get_connection() as conn:
            self.stdout.write('Retrieving entries from LDAP...')
            search = [LDAPPerson.get_search(), LDAPGroup.get_search()]
            remote_entries = get_ldap_entries(conn, search)

            self.stdout.write('Comparing local and remote database...')
            operations = sync(remote_entries, local_entries)

            if not operations:
                self.stdout.write('No differences found, exiting...')
                return

            self.stdout.write('Found the following LDAP operations that need to be applied:')
            for o in operations:
                self.stdout.write(str(o))

            # Ask for confirmation
            if not options['y']:
                y = input('Apply all operations? [y/N] ')
                if y != 'y':
                    self.stdout.write('Cancelled')
                    return

            # Apply
            self.stdout.write('Applying operations...')
            for operation in operations:
                operation.apply(conn)
