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
        # Attributes may only exist if they have a value

        # Mandatory attributes
        result = {
            'objectClass': ['esmgqGroup', 'groupOfNames', 'top'],
            'cn': [self.name],
            'qDBLinkID': [self.id],
        }

        # Optional
        if self.description:
            result['description'] = [self.description]
        if self.email:
            result['mail'] = [self.email]
        members = LDAPPerson.objects.filter(groups=self)
        if members:
            result['member'] = [m.get_dn() for m in members]

        return result

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
        # Empty values are not allowed to be in the dictionary
        result = {
            'objectClass': ['esmgqPerson', 'inetOrgPerson', 'organizationalPerson', 'person', 'top'],
            'uid': [self.username],
            'qAzureUPN': ['{}@esmgquadrivium.nl'.format(self.username.lower())],
            'qDBLinkID': [self.id],
        }
        if self.first_name:
            result['givenName'] = [self.first_name]
        if self.last_name:
            result['sn'] = [self.last_name]
        if self.get_full_name():
            result['cn'] = self.get_full_name()
        if self.email:
            result['mail'] = [self.email]
        if self.preferred_language:
            result['preferredLanguage'] = [self.preferred_language]
        gsuite_accounts = self.gsuite_accounts.all()
        if gsuite_accounts:
            result['qGSuite'] = [a.email for a in gsuite_accounts]
        return result

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
