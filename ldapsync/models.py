import re
from datetime import date
from typing import Union, Dict, List, Optional

from ldapsync.ldaputil import raise_for_multi_value
from qluis.models import Group, Person, ExternalCard, Instrument, Key, GSuiteAccount


class LdapSyncMixin:
    """Mixin for model classes to add methods for syncing with LDAP."""

    base_dn = None
    """Base DN for entries of this type in LDAP (base path)."""

    object_class = None
    """LDAP object class for entries of this type."""

    link_attribute = 'qDBLinkID'
    """LDAP attribute that stores the primary key value of the corresponding
    Django entry, for each LDAP entry."""

    attribute_keys = None
    """List/tuple of LDAP attribute keys that are defined for this type. Should
    not include the link attribute, but should include the DN attribute."""

    dn_attribute = None
    """LDAP attribute that is used for the DN."""

    def get_dn(self):
        """Construct DN for the entry."""
        dn_attribute_value = self.get_attribute_values()[self.dn_attribute][0]
        return '{attr}={val},{base_dn}'.format(attr=self.dn_attribute,
                                               val=dn_attribute_value,
                                               base_dn=self.base_dn)

    def get_attribute_values(self) -> Dict[str, List]:
        """Get attribute values in the format that LDAP expects.

        Returns:
            Dictionary of the instance attributes in LDAP directory format.
            Format of the dictionary is attribute_key -> [val1, val2, ...].
        """
        raise NotImplementedError()

    @classmethod
    def create_from_attribute_values(cls, attributes):
        """Create new instance on the database using LDAP attributes.

        Args:
            attributes: Dictionary of LDAP attributes (see ldap3 library).

        Returns:
            The created instance.
        """
        raise NotImplementedError()


class SyncedGroup(LdapSyncMixin, Group):
    class Meta:
        proxy = True

    base_dn = 'ou=groups,dc=esmgquadrivium,dc=nl'
    object_class = 'esmgqGroup'
    attribute_keys = ('cn', 'description', 'mail', 'member')
    dn_attribute = 'cn'

    @classmethod
    def create_from_attribute_values(cls, attributes):
        raise_for_multi_value(attributes['cn'],
                              attributes['description'],
                              attributes['mail'])
        instance = cls(
            name=attributes['cn'].value,
            description=attributes['description'].value or '',
            email=attributes['mail'].value or '',
        )
        instance.save()
        return instance

    def get_attribute_values(self) -> Dict[str, List]:
        return {
            'cn': [self.name],
        }


class SyncedPerson(LdapSyncMixin, Person):
    class Meta:
        proxy = True

    base_dn = 'ou=people,dc=esmgquadrivium,dc=nl'
    object_class = 'esmgqPerson'
    attribute_keys = (
        'uid',
        'givenName',
        'sn',
        'cn',
        'mail',
        'initials',
        'l',
        'street',
        'postalCode',
        'preferredLanguage',
        'qAzureUPN',
        'qBHVCertificate',
        'qCardExternalDepositMade',
        'qCardExternalDescription',
        'qCardExternalNumber',
        'qCardNumber',
        'qDateOfBirth',
        'qFieldOfStudy',
        'qFoundVia',
        'qGSuite',
        'qGender',
        'qIBAN',
        'qID',
        'qInstrumentVoice',
        'qIsStudent',
        'qKeyAccess',
        'qKeyWatcherID',
        'qKeyWatcherPIN',
        'qMemberEnd',
        'qMemberStart',
        'qPermissionExQuus',
        'qSEPADirectDebit',
        'memberOf',
        'telephoneNumber'
    )
    dn_attribute = 'uid'

    def get_attribute_values(self) -> Dict[str, List]:
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
    def create_from_attribute_values(cls, attributes):
        # Make sure that not some multi values exist
        raise_for_multi_value(attributes['uid'],
                              attributes['givenName'],
                              attributes['sn'],
                              attributes['mail'],
                              attributes['initials'],
                              attributes['l'],
                              attributes['postalCode'],
                              attributes['preferredLanguage'],
                              attributes['qCardNumber'],
                              attributes['qBHVCertificate'],
                              attributes['qCardExternalDepositMade'],
                              attributes['qCardExternalDescription'],
                              attributes['qCardExternalNumber'],
                              attributes['qDateOfBirth'],
                              attributes['qFieldOfStudy'],
                              attributes['qFoundVia'],
                              attributes['qGender'],
                              attributes['qIBAN'],
                              attributes['qID'],
                              attributes['qIsStudent'],
                              attributes['qKeyWatcherID'],
                              attributes['qKeyWatcherPIN'],
                              attributes['qMemberStart'],
                              attributes['qMemberEnd'],
                              attributes['qPermissionExQuus'],
                              attributes['qSEPADirectDebit'],
                              attributes['telephoneNumber'],
                              attributes['street'],
                              )

        def convert_birthday(ldap_value: Optional[int]) -> Optional[date]:
            if not ldap_value:
                return None
            s = str(ldap_value)
            return date(year=int(s[0:4]), month=int(s[4:6]), day=int(s[6:8]))

        instance = cls(
            username=attributes['uid'].value.lower(),
            first_name=attributes['givenName'].value or '',
            last_name=attributes['sn'].value or '',
            email=attributes['mail'].value or '',
            initials=attributes['initials'].value or '',
            city=attributes['l'].value or '',
            postal_code=attributes['postalCode'].value or '',
            preferred_language=attributes['preferredLanguage'].value or '',
            bhv_certificate=attributes['qBHVCertificate'].value,
            date_of_birth=convert_birthday(attributes['qDateOfBirth'].value),
            field_of_study=attributes['qFieldOfStudy'].value or '',
            found_via=attributes['qFoundVia'].value or '',
            gender=(attributes['qGender'].value or '').lower(),
            iban=attributes['qIBAN'].value or '',
            person_id=attributes['qID'].value or '',
            is_student=attributes['qIsStudent'].value,
            keywatcher_id=attributes['qKeyWatcherID'].value or '',
            keywatcher_pin=attributes['qKeyWatcherPIN'].value or '',
            membership_start=attributes['qMemberStart'].value,
            membership_end=attributes['qMemberEnd'].value,
            permission_exquus=attributes['qPermissionExQuus'].value,
            sepa_direct_debit=attributes['qSEPADirectDebit'].value,
            phone_number=attributes['telephoneNumber'].value or '',
            street=attributes['street'].value or '',
        )
        instance.save()

        # External cards
        external_number = attributes['qCardExternalNumber'].value
        if external_number:
            external_card, _ = ExternalCard.objects.get_or_create(
                card_number=attributes['qCardNumber'].value,
                reference_number=external_number,
                description=attributes['qCardExternalDescription'].value or ''
            )
            instance.external_card = external_card
            instance.external_card_deposit_made = attributes['qCardExternalDepositMade'].value
            instance.save()
        else:
            instance.tue_card_number = attributes['qCardNumber'].value
            instance.save()

        # Instruments
        for i in attributes['qInstrumentVoice'].values:
            instrument, _ = Instrument.objects.get_or_create(name=i.lower())
            instance.instruments.add(instrument)

        # Keys
        for k in attributes['qKeyAccess'].values:
            key, _ = Key.objects.get_or_create(number=k)
            instance.key_access.add(key)

        # Groups
        for group_dn in attributes['memberOf'].values:  # type: str
            match = re.fullmatch(r'cn=([^,]+),ou=[Gg]roups,dc=esmgquadrivium,dc=nl',
                                 group_dn.strip())
            if not match:
                raise Exception('Invalid group DN: {}'.format(group_dn))
            cn = match.group(1)
            group = Group.objects.get(name__iexact=cn)
            instance.groups.add(group)

        # GSuite accounts
        for gsuite_mail in attributes['qGSuite'].values:
            gsuite_account, _ = GSuiteAccount.objects.get_or_create(email=gsuite_mail)
            instance.gsuite_accounts.add(gsuite_account)

        return instance


SYNC_MODELS = SyncedGroup, SyncedPerson
"""Iterable of all models that can be synced with LDAP."""

SyncModel = Union[SYNC_MODELS]
"""Type for sync model to use for type hints."""
