"""Module for presenting the local Django data as an LDAP dictionary."""

from typing import Dict, List

from ldapsync.ldap import LDAPSearch, LDAPAttributeType
from members.models import QGroup, Person


class LDAPMixin:
    """Mixin for model classes to add methods for syncing with LDAP."""

    def get_dn(self) -> str:
        """Get the (normalized, i.e. lowercase) Distinguished Name for the instance."""
        raise NotImplementedError()

    def get_attributes(self) -> Dict[str, List[LDAPAttributeType]]:
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

    @classmethod
    def get_entries(cls) -> Dict[str, Dict[str, List[str]]]:
        """Get all the local database entries of this model in LDAP format."""
        return {i.get_dn(): i.get_attributes() for i in cls.objects.all()}


class LDAPGroup(LDAPMixin, QGroup):
    class Meta:
        proxy = True

    def get_dn(self):
        return 'cn={},ou=groups,dc=esmgquadrivium,dc=nl'.format(self.name.lower())

    def get_attributes(self) -> Dict[str, List[LDAPAttributeType]]:
        return {
            'objectClass': ['esmgqGroup'],
            'cn': [self.name],
            'description': [self.description],
            'mail': [self.email],
            'member': [m.get_dn() for m in LDAPPerson.objects.filter(groups=self)],
            'qDBLinkID': [self.id],
        }

    @classmethod
    def get_search(cls) -> LDAPSearch:
        return LDAPSearch(
            base_dn='ou=groups,dc=esmgquadrivium,dc=nl',
            object_class='esmgqGroup',
            attributes=[
                'objectClass',
                'cn',
                'description',
                'mail',
                'member',
                'qDBLinkID',
            ]
        )


class LDAPPerson(LDAPMixin, Person):
    class Meta:
        proxy = True

    def get_dn(self) -> str:
        return 'uid={},ou=people,dc=esmgquadrivium,dc=nl'.format(self.username.lower())

    def get_attributes(self) -> Dict[str, List[LDAPAttributeType]]:
        return {
            'objectClass': ['esmgqPerson'],
            'uid': [self.username],
            'givenName': [self.first_name],
            'sn': [self.last_name],
            'cn': [self.get_full_name()],
            'mail': [self.email],
            'preferredLanguage': [self.preferred_language],
            'qAzureUPN': ['{}@esmgquadrivium.nl'.format(self.username.lower())],
            'qGSuite': [a.email for a in self.gsuite_accounts.all()],
            'qDBLinkID': [self.id],
        }

    @classmethod
    def get_search(cls) -> LDAPSearch:
        return LDAPSearch(
            base_dn='ou=people,dc=esmgquadrivium,dc=nl',
            object_class='esmgqPerson',
            attributes=[
                'objectClass',
                'uid',
                'givenName',
                'sn',
                'cn',
                'mail',
                'preferredLanguage',
                'qAzureUPN',
                'qGSuite',
                'qDBLinkID',
            ]
        )

# class SyncLogEntry(models.Model):
#     """Log entry of a sync run."""
