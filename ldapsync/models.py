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
        # Attributes like description might have an empty string as value, in
        #     which case we should provide an empty list instead of [''].
        return {
            'objectClass': ['esmgqGroup', 'groupOfNames', 'top'],
            'cn': [self.name],
            'description': [self.description] if self.description else [],
            'mail': [self.email] if self.email else [],
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
        # Attributes like first_name might have an empty string as value, in
        #     which case we should provide an empty list instead of [''].
        return {
            'objectClass': ['esmgqPerson', 'inetOrgPerson', 'organizationalPerson', 'person', 'top'],
            'uid': [self.username],
            'givenName': [self.first_name] if self.first_name else [],
            'sn': [self.last_name] if self.last_name else [],
            'cn': [self.get_full_name()] if self.get_full_name() else [],
            'mail': [self.email] if self.email else [],
            'preferredLanguage': [self.preferred_language] if self.preferred_language else [],
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
