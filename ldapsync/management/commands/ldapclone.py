import logging
from argparse import ArgumentParser

from django.core.management import BaseCommand
from ldap3.utils.log import set_library_log_detail_level, BASIC

from ldapsync.clone import CLONE_SEARCH, clone
from ldapsync.ldap import get_ldap_entries, get_connection
from qluis.models import Instrument, GSuiteAccount, ExternalCard, Key, QGroup, Person, Membership


class Command(BaseCommand):
    help = 'Clones the full LDAP database and updates the ID attribute on LDAP.'

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('-v',
                            action='store_true',
                            help='Enable debug output.')

    def handle(self, *args, **options):
        if options['v']:
            logging.basicConfig(level=logging.DEBUG)
            set_library_log_detail_level(BASIC)

        # Clean local database
        y = input('All current Django entries will be removed. Are you sure? [y/N] ')
        if y != 'y':
            self.stdout.write('Cancelled')
            return

        Membership.objects.all().delete()
        Instrument.objects.all().delete()
        QGroup.objects.all().delete()
        Person.objects.all().delete()
        GSuiteAccount.objects.all().delete()
        ExternalCard.objects.all().delete()
        Key.objects.all().delete()

        with get_connection() as conn:
            self.stdout.write('Fetching entries from LDAP...')
            stuff = get_ldap_entries(conn, CLONE_SEARCH)
            self.stdout.write('Fetched {} entries'.format(len(stuff)))

            self.stdout.write('Saving entries to database...')
            link_updates = clone(stuff)

            self.stdout.write('Updating link attribute on the LDAP database...')
            for update in link_updates:
                update.apply(conn)
