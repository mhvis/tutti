import logging
from argparse import ArgumentParser

from django.core.management import BaseCommand
from ldap3.utils.log import set_library_log_detail_level, BASIC

from ldapsync.ldap import get_connection, get_ldap_entries
from ldapsync.models import LDAPPerson, LDAPGroup
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
        # Todo!
        # parser.add_argument('--email-on-error',
        #                     action='store_true',
        #                     help='Will send an e-mail to the administrators when an exception was raised.')

    def handle(self, *args, **options):
        if options['debug']:
            logging.basicConfig(level=logging.DEBUG)
            set_library_log_detail_level(BASIC)

        self.stdout.write('Retrieving entries from local database...')
        local_people = LDAPPerson.get_entries()
        local_groups = LDAPGroup.get_entries()

        with get_connection() as conn:
            self.stdout.write('Retrieving entries from LDAP...')
            remote_people = get_ldap_entries(conn, [LDAPPerson.get_search()])
            remote_groups = get_ldap_entries(conn, [LDAPGroup.get_search()])

            self.stdout.write('Comparing local and remote database...')
            # The people and groups need to be synced separately because they
            #  are matched on their primary key, which is only unique within
            #  people and groups, but not unique if you take those together.
            operations = sync(local_people, remote_people)
            operations += sync(local_groups, remote_groups)

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
