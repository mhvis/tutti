from argparse import ArgumentParser

from django.core.management import BaseCommand
from ldap3 import LEVEL, MODIFY_REPLACE

from ldapsync.ldaputil import get_connection
from ldapsync.models import SYNC_MODELS
from tutti.models import Instrument, GSuiteAccount, ExternalCard, Key


class Command(BaseCommand):
    help = (
        'Clones complete LDAP database into Django. '
        'Discards all current Django entries! '
        'Updates the ID attribute on LDAP.'
    )

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('--no-ldap-update',
                            action='store_true',
                            help='Does not make any changes to the LDAP database.')
        parser.add_argument('--force-ldap-id',
                            action='store_true',
                            help='Overwrite LDAP ID attribute if it already exists.')

    def handle(self, *args, **options):
        # logging.basicConfig(level=logging.DEBUG)
        # set_library_log_detail_level(BASIC)

        self.stdout.write('When you continue, all entries in Django will be removed and new entries will be')
        self.stdout.write('created from LDAP. The LDAP database is not modified apart from the ID link')
        self.stdout.write('attribute.')
        y = input('Are you sure? [y/N] ')
        if y != 'y':
            self.stdout.write('Cancelled')
            return

        with get_connection() as conn:
            # Delete current rows
            for model in SYNC_MODELS:
                model.objects.all().delete()

            # Also clear the auxiliary models
            Instrument.objects.all().delete()
            GSuiteAccount.objects.all().delete()
            ExternalCard.objects.all().delete()
            Key.objects.all().delete()

            # Retrieve from LDAP
            for model in SYNC_MODELS:
                conn.search(search_base=model.base_dn,
                            search_filter='(objectClass={})'.format(model.object_class),
                            search_scope=LEVEL,
                            attributes=list(model.attribute_keys) + [model.link_attribute])
                for entry in conn.entries:
                    self.stdout.write('Creating entry for {}...'.format(entry.entry_dn))
                    # Create Django instance
                    instance = model.create_from_attribute_values(entry)
                    if not options['no_ldap_update']:
                        # Check if LDAP ID exists already on LDAP server
                        if entry[model.link_attribute].value and not options['force_ldap_id']:
                            raise Exception('LDAP link ID attribute found on server, use --force-ldap-id to overwrite.')
                        # Update LDAP ID
                        changes = {model.link_attribute: (MODIFY_REPLACE, instance.pk)}
                        conn.modify(entry.entry_dn, changes)
