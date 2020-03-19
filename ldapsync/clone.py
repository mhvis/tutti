"""All about cloning LDAP to Django."""
import itertools
from datetime import date
from typing import Dict, List, Iterable, Tuple, Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from localflavor.generic.validators import IBANValidator
from phonenumber_field.validators import validate_international_phonenumber

from ldapsync.ldap import LDAPSearch, LDAPAttributeType
from ldapsync.ldapoperations import LDAPOperation, ModifyOperation
from members.models import QGroup, Person, GSuiteAccount, Instrument, Key, ExternalCard, ExternalCardLoan, \
    GroupMembership

CURRENT_MEMBERS_GROUP = 'cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl'
"""Distinguished name for the group that stores current Quadrivium members."""

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
"""Specification of LDAP search for cloning."""


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


def _get_val(attrs, key, default=None):
    """Get value for the single-valued attribute or default."""
    vals = attrs.get(key, [])
    return vals[0] if vals else default


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

    Checks:
    * (person is in 'Huidige leden' group) iff (is_set(qMemberStart) and is_not_set(qMemberEnd))
    * not (is_set(qMemberEnd) and is_not_set(qMemberStart))
    """
    current_members_entry = ldap_entries.get(CURRENT_MEMBERS_GROUP, {})
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
    for dn, attrs in _iterate_people(ldap_entries):
        cn = _get_val(attrs, 'cn', default='')
        given_name = _get_val(attrs, 'givenName', default='')
        sn = _get_val(attrs, 'sn', default='')
        if '{} {}'.format(given_name, sn).strip() != cn:
            yield 'givenName+sn != cn for person {}'.format(dn)

        uid = _get_val(attrs, 'uid', default='').lower()
        azure_upn = _get_val(attrs, 'qAzureUPN', default='').lower()
        if azure_upn and azure_upn != '{}@esmgquadrivium.nl'.format(uid):
            yield 'Invalid qAzureUPN for person {}'.format(dn)


def check_required_uid(ldap_entries) -> Iterable[str]:
    """Uid (username) is required for all people entries."""
    for dn, attrs in _iterate_people(ldap_entries):
        uid = _get_val(attrs, 'uid')
        if not uid:
            yield 'Missing uid for person {}'.format(dn)


def check_iban_phone(ldap_entries) -> Iterable[str]:
    """Check if IBAN and phone number are valid (otherwise cloning will fail as well)."""
    validate_iban = IBANValidator()
    for dn, attrs in _iterate_people(ldap_entries):
        try:
            validate_iban(_get_val(attrs, 'qIBAN'))
            validate_international_phonenumber(_get_val(attrs, 'telephoneNumber'))
        except ValidationError as e:
            yield 'Phone or IBAN error for person {}: {}'.format(dn, e)


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
    issues.extend(check_required_uid(ldap_entries))
    issues.extend(check_iban_phone(ldap_entries))
    return issues


def _parse_birthday(ldap_value: Optional[int]) -> Optional[date]:
    """Parse LDAP birthday integer to date object."""
    if not ldap_value:
        return None
    s = str(ldap_value)
    return date(year=int(s[0:4]), month=int(s[4:6]), day=int(s[6:8]))


def create_person_and_related(attrs, q_member_group: QGroup) -> Person:
    """Creates a person from LDAP data.

    Also creates related instances like keys, instruments.

    Args:
        attrs: LDAP attributes for a person entry.
        q_member_group: Group that stores Q memberships.
    """
    ext1 = _get_val(attrs, 'qCardExternalDepositMade')
    ext2 = _get_val(attrs, 'qCardExternalDescription')
    ext3 = _get_val(attrs, 'qCardExternalNumber')
    has_external_card = ext1 is not None or ext2 or ext3  # (ext1 might be False instead of None)

    # Create person
    person = Person.objects.create(
        first_name=_get_val(attrs, 'givenName', ''),
        last_name=_get_val(attrs, 'sn', ''),
        username=_get_val(attrs, 'uid', '').lower(),
        bhv_certificate=_get_val(attrs, 'qBHVCertificate', None),
        date_of_birth=_parse_birthday(_get_val(attrs, 'qDateOfBirth')),
        field_of_study=_get_val(attrs, 'qFieldOfStudy', ''),
        gender=_get_val(attrs, 'qGender', '').lower(),
        iban=_get_val(attrs, 'qIBAN', ''),
        person_id=_get_val(attrs, 'qID', ''),
        is_student=_get_val(attrs, 'qIsStudent', None),
        keywatcher_id=_get_val(attrs, 'qKeyWatcherID', ''),
        keywatcher_pin=_get_val(attrs, 'qKeyWatcherPIN', ''),
        sepa_direct_debit=_get_val(attrs, 'qSEPADirectDebit', None),
        initials=_get_val(attrs, 'initials', ''),
        city=_get_val(attrs, 'l', ''),
        email=_get_val(attrs, 'mail', ''),
        postal_code=_get_val(attrs, 'postalCode', ''),
        preferred_language=_get_val(attrs, 'preferredLanguage', ''),
        street=_get_val(attrs, 'street', ''),
        phone_number=_get_val(attrs, 'telephoneNumber', ''),
        tue_card_number=_get_val(attrs, 'qCardNumber') if not has_external_card else None,
    )

    # Create related instances
    # GSuite
    for mailbox in attrs.get('qGSuite', []):
        account, _ = GSuiteAccount.objects.get_or_create(email=mailbox.lower())
        person.gsuite_accounts.add(account)
    # Instruments
    for i in attrs.get('qInstrumentVoice', []):
        instrument, _ = Instrument.objects.get_or_create(name=i.lower())
        person.instruments.add(instrument)
    # Key access
    for k in attrs.get('qKeyAccess', []):
        key, _ = Key.objects.get_or_create(number=k)
        person.key_access.add(key)
    # Set Q membership
    member_start = _get_val(attrs, 'qMemberStart')
    member_end = _get_val(attrs, 'qMemberEnd')
    if member_start and member_end:
        # For past memberships, only create a historical record
        GroupMembership.objects.create(
            group=q_member_group,
            user=person,
            start=member_start,
            end=member_end
        )
    elif member_start:
        # For current memberships, add person to group
        person.groups.add(q_member_group)
        # Update the automatically created GroupMembership start date
        membership = GroupMembership.objects.get(group=q_member_group, user=person, end=None)
        membership.start = member_start
        membership.save()

    # External card
    if has_external_card:
        external_card, _ = ExternalCard.objects.get_or_create(
            card_number=_get_val(attrs, 'qCardNumber', None),
            reference_number=_get_val(attrs, 'qCardExternalNumber', None),
            description=_get_val(attrs, 'qCardExternalDescription', ''),
        )
        deposit = _get_val(attrs, 'qCardExternalDepositMade', None)
        ExternalCardLoan.objects.create(
            external_card=external_card,
            person=person,
            deposit_made='' if deposit is None else 'y?' if deposit else 'n?'
        )
    return person


def create_group_and_memberships(attrs: Dict, people: Dict[str, Person]) -> QGroup:
    """Create a group and memberships from LDAP data.

    Args:
        attrs: LDAP attributes for the group.
        people: Dictionary of DN -> Person instance.
    """
    group = QGroup.objects.create(name=_get_val(attrs, 'cn', ''),
                                  description=_get_val(attrs, 'description', ''),
                                  email=_get_val(attrs, 'mail', ''),
                                  owner=people.get(_get_val(attrs, 'owner')))
    # Create group memberships
    for member in attrs.get('member', []):
        person = people[member.lower()]
        person.groups.add(group)
    return group


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
    # Check for issues
    issues = check_for_issues(ldap_entries)
    if issues:
        raise CloneError(issues)

    created_people = {}
    created_groups = {}

    # Do import
    with transaction.atomic():
        # Create current members group
        q_member_group = QGroup.objects.create(name='Huidige leden', email='leden@esmgquadrivium.nl')
        created_groups[CURRENT_MEMBERS_GROUP] = q_member_group

        # Create people
        for dn, attrs in _iterate_people(ldap_entries):
            created_people[dn] = create_person_and_related(attrs, q_member_group)

        # Create groups
        for dn, attrs in _iterate_groups(ldap_entries):
            if dn == CURRENT_MEMBERS_GROUP:
                continue
            created_groups[dn] = create_group_and_memberships(attrs, created_people)

    # Return LDAP operations
    created = itertools.chain(created_people.items(), created_groups.items())
    return [ModifyOperation(dn, link_attribute, [instance.id]) for dn, instance in created]
