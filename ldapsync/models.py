"""Module for presenting the local Django data as an LDAP dictionary."""

from typing import Dict, List

from ldapsync.ldap import LDAPSearch
from qluis.models import QGroup, Person


class LDAPMixin:
    """Mixin for model classes to add methods for syncing with LDAP."""

    def get_dn(self) -> str:
        """Get the Distinguished Name for the instance."""
        raise NotImplementedError()

    def get_attributes(self) -> Dict[str, List]:
        """Get the LDAP attribute values.

        Returns:
            Dictionary of the instance attributes in LDAP directory format.
            Format of the dictionary is attribute_key -> [val1, val2, ...].
        """
        raise NotImplementedError()

    @classmethod
    def get_search(cls) -> LDAPSearch:
        """Get search parameters for retrieval of LDAP data."""
        raise NotImplementedError()


class LDAPGroup(LDAPMixin, QGroup):
    class Meta:
        proxy = True

    def get_dn(self):
        pass

    def get_attributes(self) -> Dict[str, List]:
        return {
            'objectClass': ['esmgqGroup'],
            'cn': [self.name],
        }

    @classmethod
    def get_search(cls) -> LDAPSearch:
        pass


class LDAPPerson(LDAPMixin, Person):
    class Meta:
        proxy = True

    def get_dn(self) -> str:
        pass

    def get_attributes(self) -> Dict[str, List]:
        return {
            'uid': [self.username],
            'givenName': [self.first_name],
            'sn': [self.last_name],
            'cn': [self.get_full_name()],
            'mail': [self.email],
            'initials': [self.initials],
            'l': [self.city],
            'postalCode': [self.postal_code],
            'preferredLanguage': [self.preferred_language],
            'qAzureUPN': ['{}@esmgquadrivium.nl'.format(self.username.lower())],

        }

    @classmethod
    def get_search(cls) -> LDAPSearch:
        pass


def get_local_entries() -> Dict[str, Dict[str, List[str]]]:
    """Get the local database entries in LDAP format."""
    entries = {p.get_dn(): p.get_attributes() for p in LDAPPerson.objects.all()}
    entries.update({g.get_dn(): g.get_attributes() for g in LDAPGroup.objects.all()})
    return entries

# class SyncLogEntry(models.Model):
#     """Log entry of a sync run."""
