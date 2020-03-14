"""All about cloning LDAP to Django."""
from typing import Dict, List, Iterable, Tuple

from django.db import transaction

from ldapsync.ldap import LDAPSearch, LDAPAttributeType
from ldapsync.ldapoperations import LDAPOperation

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


class CloneError(ValueError):
    """Exception raised for problems in the input data."""
    pass


def _iterate_groups(ldap_entries) -> Iterable[Tuple[str, Dict]]:
    """Iterate over group entry items."""
    for dn, attrs in ldap_entries.items():
        if dn.endswith('ou=groups,dc=esmgquadrivium,dc=nl'):
            yield dn, attrs


def _iterate_people(ldap_entries) -> Iterable[Tuple[str, Dict]]:
    """Iterate over person entry items."""
    for dn, attrs in ldap_entries.items():
        if dn.endswith('ou=people,dc=esmgquadrivium,dc=nl'):
            yield dn, attrs


def check_multi_values(ldap_entries) -> Iterable[str]:
    """Check for attributes that may not have multiple values."""
    single_valued = {  # Set of attributes that should be single valued
        # Person attributes
        'cn', 'sn', 'givenName', 'qAzureUPN', 'qBHVCertificate', 'qCardExternalDepositMade', 'qCardExternalDescription',
        'qCardExternalNumber', 'qCardNumber', 'qDateOfBirth', 'qFieldOfStudy', 'qGender', 'qIBAN', 'qID', 'qIsStudent',
        'qKeyWatcherID', 'qKeyWatcherPIN', 'qMemberEnd', 'qMemberStart', 'qSEPADirectDebit', 'initials', 'l', 'mail',
        'postalCode', 'preferredLanguage', 'street', 'telephoneNumber', 'uid',
        # Group attributes
        'cn', 'description', 'mail', 'owner',
    }
    # Go over all attributes
    for dn, attribute in ldap_entries.items():
        for key, values in attribute.items():
            if key in single_valued and len(values) > 1:
                # Multi-valued attribute found
                yield 'Attribute {} on {} has multiple values ({})'.format(key, dn, values)


def check_group_members(ldap_entries) -> Iterable[str]:
    """Check if all group members have a corresponding person entry."""
    for dn, attributes in _iterate_groups(ldap_entries):
        members = attributes.get('member', [])
        for member_dn in members:
            if member_dn.lower() not in ldap_entries:
                yield 'Unknown member DN found in group {}, member DN is {}'.format(dn, member_dn)


def check_q_membership(ldap_entries) -> Iterable[str]:
    """Check Q membership consistency.

    Checks: (person is in 'Huidige leden' group) iff (is_set(qMemberStart) and is_not_set(qMemberEnd))
    """
    current_members_entry = ldap_entries.get('cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl', {})
    current_member_dns = current_members_entry.get('member', [])
    current_member_set = {m.lower() for m in current_member_dns}
    # Go over all people and check their qMemberStart/qMemberEnd
    for dn, attributes in _iterate_people(ldap_entries):
        has_start = len(attributes.get('qMemberStart', [])) == 1
        has_end = len(attributes.get('qMemberEnd', [])) == 1
        in_group = dn in current_member_set  # Whether the person is in the current members group
        if has_start and not has_end:
            if not in_group:
                yield 'Person {} has qMemberStart but is not in current members group'.format(dn)
        elif not has_start and has_end:
            yield 'Person {} has only qMemberEnd set'.format(dn)
        else:
            if in_group:
                yield 'Person {} has incorrect qMemberStart/end but is in current members group'.format(dn)


def check_name_azure_upn(ldap_entries) -> Iterable[str]:
    """Check for value consistency between duplicated values.

    Checks: givenName+" "+sn == cn and qAzureUPN startswith uid
    """

    def _get_string_val(attrs, key):
        """Get value or ''."""
        vals = attrs.get(key, [])
        return vals[0] if vals else ''

    for dn, attrs in _iterate_people(ldap_entries):
        cn = _get_string_val(attrs, 'cn')
        given_name = _get_string_val(attrs, 'givenName')
        sn = _get_string_val(attrs, 'sn')
        if '{} {}'.format(given_name, sn).strip() != cn:
            yield 'givenName+sn != cn for person {}'.format(dn)

        uid = _get_string_val(attrs, 'uid').lower()
        azure_upn = _get_string_val(attrs, 'qAzureUPN').lower()
        if azure_upn and azure_upn != '{}@esmgquadrivium.nl'.format(uid):
            yield 'Invalid qAzureUPN for person {}'.format(dn)


def check_for_issues(ldap_entries: Dict[str, Dict[str, List[LDAPAttributeType]]]) -> List[str]:
    """Check for all possible issues/inconsistencies with given LDAP data.

    Args:
        ldap_entries: The people/group entries. The dictionary must be
            normalized (all DNs are lowercase)!

    Returns:
        A list of issues, if there are no issues the list will be empty.
    """
    issues = []
    issues.extend(check_multi_values(ldap_entries))
    issues.extend(check_group_members(ldap_entries))
    issues.extend(check_q_membership(ldap_entries))
    issues.extend(check_name_azure_upn(ldap_entries))
    return issues


def clone(ldap_entries: Dict[str, Dict[str, List[LDAPAttributeType]]],
          link_attribute='qDBLinkID') -> List[LDAPOperation]:
    """Create Django model instances from LDAP entries.

    Next to the entries, this will always create a current members group
    (huidige leden) even if that group would have no members.

    Args:
        ldap_entries: All people and groups from the LDAP database as entries.
        link_attribute: LDAP attribute that stores the Django instance ID.

    Returns:
        LDAP operations that will update the link attribute in LDAP.

    Raises:
        CloneError: When there are problems with the LDAP data.
    """
    issues = check_for_issues(ldap_entries)
    if issues:
        raise CloneError(issues)

    # All (or most) checks done, do the actual import
    with transaction.atomic():
        # Create current members group
        # members_group = QGroup.objects.create(name='Huidige leden', email='leden@esmgquadrivium.nl')
        pass
    pass


# TODO: implement clone() using the legacy code below
"""
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
        instance = cls(
            name=attributes['cn'].value,
            description=attributes['description'].value or '',
            email=attributes['mail'].value or '',
        )
        instance.save()
        return instance

"""
