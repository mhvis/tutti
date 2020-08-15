"""Module for presenting the local Django data as LDAP entities."""

from typing import Dict, List

from django.db.models import QuerySet

from sync.ldap import LDAPSearch, LDAPAttributeType
from members.models import QGroup, Person


class LDAPEntity:
    """Interface to Django model entry data for LDAP sync."""

    # Django model class corresponding to this entity.
    model = None

    def __init__(self, instance: model):
        """Constructs instance.

        Args:
            instance: Django model instance. Should be of the same type as the
                given model class.
        """
        self.instance = instance

    def get_dn(self) -> str:
        """Gets the (normalized, i.e. lowercase) Distinguished Name for the instance."""
        raise NotImplementedError()

    def get_attributes(self) -> Dict[str, List[LDAPAttributeType]]:
        """Gets the LDAP attribute values.

        Returns:
            Dictionary of the instance attributes in LDAP directory format.
            Format of the dictionary is attribute_key -> [val1, val2, ...].
        """
        raise NotImplementedError()

    @classmethod
    def get_search(cls) -> LDAPSearch:
        """Gets search parameters for retrieval of LDAP data."""
        raise NotImplementedError()

    @classmethod
    def get_entries(cls) -> Dict[str, Dict[str, List[str]]]:
        """Gets all the local database entries of this model in LDAP format."""
        return {i.get_dn(): i.get_attributes() for i in cls.from_queryset(cls.model.objects.all())}

    @classmethod
    def from_queryset(cls, qs: QuerySet) -> List:
        """Returns a list of LDAPEntity instances from a queryset."""
        return [cls(i) for i in qs]


class LDAPGroup(LDAPEntity):
    model = QGroup

    def get_dn(self):
        return 'cn={},ou=groups,dc=esmgquadrivium,dc=nl'.format(self.instance.name.lower())

    def get_attributes(self) -> Dict[str, List[LDAPAttributeType]]:
        # Attributes may only exist if they have a value

        # Mandatory attributes
        result = {
            'objectClass': ['esmgqGroup', 'groupOfNames', 'top'],
            'cn': [self.instance.name],
            'qDBLinkID': [self.instance.id],
        }

        # Optional
        if self.instance.description:
            result['description'] = [self.instance.description]
        if self.instance.email:
            result['mail'] = [self.instance.email]
        members = LDAPPerson.from_queryset(Person.objects.filter(groups=self.instance))
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


class LDAPPerson(LDAPEntity):
    model = Person

    def get_dn(self) -> str:
        return 'uid={},ou=people,dc=esmgquadrivium,dc=nl'.format(self.instance.username.lower())

    def get_attributes(self) -> Dict[str, List[LDAPAttributeType]]:
        # Empty values are not allowed to be in the dictionary
        result = {
            'objectClass': ['esmgqPerson', 'inetOrgPerson', 'organizationalPerson', 'person', 'top'],
            'uid': [self.instance.username],
            'qAzureUPN': ['{}@esmgquadrivium.nl'.format(self.instance.username.lower())],
            'qDBLinkID': [self.instance.id],
        }
        if self.instance.first_name:
            result['givenName'] = [self.instance.first_name]
        if self.instance.last_name:
            result['sn'] = [self.instance.last_name]
        if self.instance.get_full_name():
            result['cn'] = [self.instance.get_full_name()]
        if self.instance.email:
            result['mail'] = [self.instance.email]
        if self.instance.preferred_language:
            result['preferredLanguage'] = [self.instance.preferred_language]
        if self.instance.ldap_password:
            # userPassword is stored as a bytes object in LDAP, we encode with UTF-8
            result['userPassword'] = [self.instance.ldap_password.encode()]
        gsuite_accounts = self.instance.gsuite_accounts.all()
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
                'userPassword',
            ]
        )
