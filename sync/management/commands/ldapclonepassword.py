from collections import namedtuple

from django.core.management import BaseCommand

from members.models import Person
from sync.ldap import get_ldap_entries, get_connection, LDAPSearch


class Command(BaseCommand):
    def handle(self, *args, **options):
        with get_connection() as conn:
            # Fetch LDAP passwords
            self.stdout.write('Fetching passwords from LDAP...')
            stuff = get_ldap_entries(conn, [LDAPSearch(base_dn='ou=people,dc=esmgquadrivium,dc=nl',
                                                       object_class='esmgqPerson',
                                                       attributes=['qDBLinkID', 'userPassword', 'uid'])])
            self.stdout.write('Fetched {} entries'.format(len(stuff)))

        # Match up people
        Update = namedtuple("Update", ["person", "new_ldap_password", "ldap_username"])
        updates = []
        for dn, values in stuff.items():
            if "qDBLinkID" not in values or "userPassword" not in values:
                self.stdout.write("Not updated: {}".format(values["uid"][0]))
                continue
            person = Person.objects.get(id=values["qDBLinkID"][0])
            updates.append(Update(person=person,
                                  new_ldap_password=values["userPassword"][0].decode("utf-8"),
                                  ldap_username=values["uid"][0]))
        self.stdout.write("Updates:")
        for u in updates:
            self.stdout.write("* {}".format(u))

        y = input('Proceed with saving the passwords? [y/N] ')
        if y != 'y':
            self.stdout.write('Cancelled')
            return

        for u in updates:
            u.person.ldap_password = u.new_ldap_password
            u.person.password = "invalid"
            u.person.save()
