import logging
from argparse import ArgumentParser

from django.core.management import BaseCommand
from ldap3.utils.log import set_library_log_detail_level, BASIC

from sync.ldap import get_connection
from sync.ldapsync import get_ldap_sync_operations


class Command(BaseCommand):
    help = 'One-way sync local database to remote LDAP database. Only modifies LDAP database.'

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('--debug',
                            action='store_true',
                            help='Enable ldap3 debug output.')

    def handle(self, *args, **options):
        # Setup debug output
        if options['debug']:
            logging.basicConfig(level=logging.DEBUG)
            set_library_log_detail_level(BASIC)

        # Do sync in interactive style
        with get_connection() as conn:
            self.stdout.write('Comparing local and remote entries...')
            operations = get_ldap_sync_operations(conn)
            if not operations:
                self.stdout.write('No differences found, exiting...')
                return

            self.stdout.write('Found the following LDAP operations that need to be applied:')
            for o in operations:
                self.stdout.write(str(o))

            # Ask for confirmation
            y = input('Apply all operations? [y/N] ')
            if y != 'y':
                self.stdout.write('Cancelled')
                return

            # Apply
            self.stdout.write('Applying operations...')
            for operation in operations:
                operation.apply(conn)
