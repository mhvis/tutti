"""All about cloning LDAP to Django."""
from typing import Dict, List

from ldapsync.ldap import LDAPSearch
from ldapsync.ldapoperations import LDAPOperation


def _raise_for_multi_value(*attributes):
    """Raise exception when a given attribute has more than one values."""
    pass
    # for a in attributes:
    #     if len(a.values) > 1:
    #         raise Exception('Attribute {} for entry {} has more than one values.'.format(a, a.entry))


# Specification of LDAP search for cloning
CLONE_SEARCH = (
    LDAPSearch(
        base_dn='ou=people,dc=esmgquadrivium,dc=nl',
        object_class='esmgqPerson',
        attributes=[
            'cn',
            'sn',
            'givenName',
            'qAzureUPN',
            'qBHVCertificate',
            'qCardExternalDepositMade',
            'qCardExternalDescription',
            'qCardExternalNumber',
            'qCardNumber',
            'qDateOfBirth',
            'qFieldOfStudy',
            # 'qFoundVia',
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
            # 'qPermissionExQuus',
            # 'qPermissionMedia',
            'qSEPADirectDebit',
            'initials',
            'l',
            'mail',
            'postalCode',
            'preferredLanguage',
            'street',
            'telephoneNumber',
            'uid',
            # 'userPassword',
        ]),
    LDAPSearch(
        base_dn='ou=groups,dc=esmgquadrivium,dc=nl',
        object_class='esmgqGroup',
        attributes=[
            'cn',
            'description',
            'mail',
            'member',
            'owner',
        ]),
)


def clone(ldap_entries: Dict[str, Dict[str, List[str]]],
          link_attribute='qDBLinkID') -> List[LDAPOperation]:
    """Create Django model instances from LDAP entries.

    Args:
        ldap_entries: All people and groups from the LDAP database as entries.
        link_attribute: LDAP attribute that stores the Django instance ID.

    Returns:
        LDAP operations that will update the link attribute in LDAP.
    """
    pass


# TODO: implement clone() using the legacy code below
"""
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
    cur_memberships = Membership.objects.filter(person__username__iexact=instance.username,
                                                group__name__iexact=cn,
                                                end__isnull=True)
    if cur_memberships.count() == 0:
        Membership.objects.create(group=group, person=instance)

# GSuite accounts
for gsuite_mail in attributes['qGSuite'].values:
    gsuite_account, _ = GSuiteAccount.objects.get_or_create(email=gsuite_mail)
    instance.gsuite_accounts.add(gsuite_account)

return instance


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

"""
