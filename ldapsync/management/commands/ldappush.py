from argparse import ArgumentParser

from django.core.management import BaseCommand

from ldapsync.ldaputil import get_connection
from ldapsync.sync import get_sync_operations, apply_sync


class Command(BaseCommand):
    help = 'One-way sync Django database to LDAP database. Only modifies LDAP database.'

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('-y',
                            action='store_true',
                            help='Directly apply sync without asking for confirmation.')

    def handle(self, *args, **options):
        # logging.basicConfig(level=logging.DEBUG)
        # set_library_log_detail_level(BASIC)
        with get_connection() as conn:
            self.stdout.write('Finding differences between databases...')
            operations = get_sync_operations(conn)
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
            apply_sync(conn, operations)
