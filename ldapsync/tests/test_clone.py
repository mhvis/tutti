from datetime import datetime, date

from django.db.models import Q
from django.test import TestCase
from django.utils import timezone

from ldapsync.clone import clone, CloneError
from ldapsync.ldapoperations import ModifyOperation
from members.models import Person, QGroup, GroupMembership, Instrument, ExternalCard, ExternalCardLoan, GSuiteAccount, \
    Key


class CloneTestCase(TestCase):
    """Test cloning of LDAP data to local database."""

    def test_minimal(self):
        """Cloning should work for minimal entry."""
        entries = {
            'uid=aperson,ou=people,dc=esmgquadrivium,dc=nl': {'uid': ['aperson']},
            'cn=agroup,ou=groups,dc=esmgquadrivium,dc=nl': {'cn': ['agroup']},
        }
        clone(entries)
        self.assertEqual(1, Person.objects.all().count())
        self.assertEqual(2, QGroup.objects.all().count())  # Includes 'current members' group
        self.assertEqual(0, Person.objects.first().groups.count())  # Person is not member of any group
        self.assertEqual(0, GroupMembership.objects.count())
        self.assertEqual('aperson', Person.objects.first().username)
        self.assertEqual('agroup', QGroup.objects.get(name='agroup').name)

    def test_multiple_values(self):
        """Cloning should fail if any of these attributes has multiple values."""
        # Try all person single-valued attributes
        person_attrs = ['cn', 'sn', 'givenName', 'qAzureUPN', 'qBHVCertificate', 'qCardExternalDepositMade',
                        'qCardExternalDescription', 'qCardExternalNumber', 'qCardNumber', 'qDateOfBirth',
                        'qFieldOfStudy', 'qGender', 'qIBAN', 'qID', 'qIsStudent', 'qKeyWatcherID', 'qKeyWatcherPIN',
                        'qMemberEnd', 'qMemberStart', 'qSEPADirectDebit', 'initials', 'l', 'mail', 'postalCode',
                        'preferredLanguage', 'street', 'telephoneNumber', 'uid']
        for attr in person_attrs:
            entries = {'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {'uid': ['test']}}
            entries['uid=test,ou=people,dc=esmgquadrivium,dc=nl'][attr] = ['avalue', 'anothervalue']
            with self.assertRaises(CloneError):
                clone(entries)
        # Try all group attributes that are single-valued
        group_attrs = ['cn', 'description', 'mail', 'owner']
        for attr in group_attrs:
            entries = {'cn=test,ou=groups,dc=esmgquadrivium,dc=nl': {'cn': ['test']}}
            entries['cn=test,ou=groups,dc=esmgquadrivium,dc=nl'][attr] = ['avalue', 'anothervalue']
            with self.assertRaises(CloneError):
                clone(entries)

    def test_inconsistent_name(self):
        """Cloning should fail if givenName+sn != cn."""
        entries = {'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
            'uid': ['test'],
            'givenName': ['Maarten'],
            'sn': ['Visscher'],
            'cn': ['Wessel']}
        }
        with self.assertRaises(CloneError):
            clone(entries)

    def test_azure_upn(self):
        """Azure UPN should be same as username."""
        entries = {'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
            'uid': ['test'],
            'qAzureUPN': ['fail@esmgquadrivium.nl'],
        }}
        with self.assertRaises(CloneError):
            clone(entries)

    def test_external_card(self):
        """External cards in LDAP should result in an ExternalCard+ExternalCardLoan instance."""
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
                'qCardNumber': [1234567],
                'qCardExternalNumber': [5],
                'qCardExternalDescription': ['Cluster 3'],
                'qCardExternalDepositMade': [True],
            }
        }
        clone(entries)
        # Check if ExternalCard+ExternalCardLoan are correctly created
        self.assertEqual(1, ExternalCard.objects.count())
        self.assertEqual(1, ExternalCardLoan.objects.count())
        card = ExternalCard.objects.first()
        loan = ExternalCardLoan.objects.first()
        self.assertEqual(1234567, card.card_number)
        self.assertEqual(5, card.reference_number)
        self.assertEqual('Cluster 3', card.description)
        self.assertIsNone(loan.end)
        self.assertEqual('y?', loan.deposit_made)
        # Make sure that TU/e card number is NOT set!
        self.assertIsNone(Person.objects.first().tue_card_number)

    def test_date_of_birth(self):
        """Test conversion of date of birth."""
        entries = {'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
            'uid': ['test'],
            'qDateOfBirth': [19951226],
        }}
        clone(entries)
        self.assertEqual(date(1995, 12, 26), Person.objects.first().date_of_birth)

    def test_inconsistent_membership(self):
        """Clone should fail if member start/end is inconsistent with 'current members' group."""
        # Has qMemberStart+qMemberEnd, so should not be in current members group
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
                'qMemberStart': [datetime(2010, 2, 2)],
                'qMemberEnd': [datetime(2010, 5, 2)],
            },
            'cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['Huidige leden'],
                'member': ['uid=TEst,ou=people,dc=esmgquadrivium,dc=nl'],
            }
        }
        with self.assertRaises(CloneError):
            clone(entries)

        # Has no qMemberStart+qMemberEnd, so should not be in current members group
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
            },
            'cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['Huidige leden'],
                'member': ['uid=test,ou=people,dc=esmgquadrivium,dc=nl'],
            }
        }
        with self.assertRaises(CloneError):
            clone(entries)

        # Has only qMemberStart, so should be in current members group
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
                'qMemberStart': [datetime(2010, 2, 2)],
            },
            'cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['Huidige leden'],
                'member': [],
            }
        }
        with self.assertRaises(CloneError):
            clone(entries)

        # Has only qMemberEnd, should raise error
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
                'qMemberEnd': [datetime(2010, 2, 2)],
            },
        }
        with self.assertRaises(CloneError):
            clone(entries)

    def test_member_start_end(self):
        """Test conversion of former member with both qMemberStart and qMemberEnd to group membership."""
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
                'qMemberStart': [datetime(2010, 2, 2, tzinfo=timezone.utc)],
                'qMemberEnd': [datetime(2010, 5, 2, tzinfo=timezone.utc)],
            },
            'cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['Huidige leden'],
                'member': [],
            }
        }
        clone(entries)
        self.assertEqual(1, Person.objects.count())
        self.assertEqual(1, QGroup.objects.count())
        self.assertEqual(0, Person.objects.first().groups.count())  # Person is not a current group member
        self.assertEqual(1, GroupMembership.objects.count())
        membership = GroupMembership.objects.first()
        self.assertEqual(datetime(2010, 2, 2, tzinfo=timezone.utc), membership.start)
        self.assertEqual(datetime(2010, 5, 2, tzinfo=timezone.utc), membership.end)

    def test_member_start(self):
        """Test conversion of a current member with only qMemberStart to group membership."""
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
                'qMemberStart': [datetime(2010, 2, 2, tzinfo=timezone.utc)],
            },
            'cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['Huidige leden'],
                'member': ['uid=test,ou=people,dc=esmgquadrivium,dc=nl'],
            }
        }
        clone(entries)
        self.assertEqual(1, QGroup.objects.count())
        self.assertEqual(1, Person.objects.count())
        self.assertEqual(1, Person.objects.first().groups.count())  # Person is a current group member
        self.assertEqual(1, GroupMembership.objects.count())
        membership = GroupMembership.objects.first()
        self.assertEqual(datetime(2010, 2, 2, tzinfo=timezone.utc), membership.start)
        self.assertIsNone(membership.end)

    def test_group_membership(self):
        """Test group membership conversion."""
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
            },
            'cn=agroup,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['agroup'],
                'member': ['uid=test,ou=people,dc=esmgquadrivium,dc=nl'],
            }
        }
        clone(entries)
        self.assertEqual(2, QGroup.objects.count())  # 2 groups because there's also a current members group
        self.assertEqual(1, Person.objects.count())
        self.assertEqual(1, Person.objects.first().groups.count())
        self.assertEqual(1, GroupMembership.objects.count())
        membership = GroupMembership.objects.first()
        self.assertIsNone(membership.end)

    def test_full_person(self):
        """Test a person with (almost) all attributes."""
        entries = {
            'cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['Huidige leden'],
                'member': ['uid=gustav,ou=people,dc=esmgquadrivium,dc=nl']
            },
            'uid=gustav,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['gustav'],
                'cn': ['Gustav Mahler'],
                'sn': ['Mahler'],
                'givenName': ['Gustav'],
                'qAzureUPN': ['gustav@esmgquadrivium.nl'],
                'qBHVCertificate': [datetime(2020, 1, 1)],
                'qCardNumber': [1234567],
                'qDateOfBirth': [18600707],
                'qFieldOfStudy': ['Alma'],
                'qGSuite': ['gustav@esmgquadrivium.nl', 'mahler@esmgquadrivium.nl'],
                'qGender': ['Male'],
                'qIBAN': ['NL45ABNA9574218201'],
                'qID': ['GUSMAL'],
                'qInstrumentVoice': ['Piano', 'conducting'],
                'qIsStudent': [True],
                'qKeyAccess': [15, 27],
                'qKeyWatcherID': ['1234'],
                'qKeyWatcherPIN': ['5678'],
                'qMemberStart': [datetime(2010, 1, 1, tzinfo=timezone.utc)],
                'qSEPADirectDebit': [True],
                'initials': ['G.'],
                'l': ['Prague'],
                'mail': ['gustav@hofoper.at'],
                'postalCode': ['1111XX'],
                'preferredLanguage': ['en-us'],
                'street': ['Eine Strasse 1'],
                'telephoneNumber': ['+43654365434680'],
            },
        }
        clone(entries)
        # Check if the number of rows is correct
        self.assertEqual(1, QGroup.objects.count())  # 'Huidige leden' group
        self.assertEqual(1, Person.objects.count())
        self.assertEqual(2, Instrument.objects.count())
        self.assertEqual(0, ExternalCard.objects.count())
        self.assertEqual(0, ExternalCardLoan.objects.count())
        self.assertEqual(2, GSuiteAccount.objects.count())
        self.assertEqual(2, Key.objects.count())
        self.assertEqual(1, GroupMembership.objects.count())
        # Check the values
        gustav = Person.objects.first()  # type: Person
        self.assertEqual('gustav', gustav.username)
        self.assertEqual('Gustav', gustav.first_name)
        self.assertEqual('Mahler', gustav.last_name)
        self.assertEqual(date(2020, 1, 1), gustav.bhv_certificate)
        self.assertEqual(1234567, gustav.tue_card_number)
        self.assertEqual(date(1860, 7, 7), gustav.date_of_birth)
        self.assertEqual('Alma', gustav.field_of_study)
        self.assertCountEqual(['gustav@esmgquadrivium.nl', 'mahler@esmgquadrivium.nl'],
                              [a.email for a in gustav.gsuite_accounts.all()])
        self.assertEqual('male', gustav.gender)
        self.assertEqual('NL45ABNA9574218201', gustav.iban)
        self.assertEqual('GUSMAL', gustav.person_id)
        self.assertCountEqual(['piano', 'conducting'],
                              [i.name for i in gustav.instruments.all()])
        self.assertTrue(gustav.is_student)
        self.assertCountEqual([15, 27],
                              [k.number for k in gustav.key_access.all()])
        self.assertEqual('1234', gustav.keywatcher_id)
        self.assertEqual('5678', gustav.keywatcher_pin)
        self.assertTrue(gustav.sepa_direct_debit)
        self.assertEqual('G.', gustav.initials)
        self.assertEqual('Prague', gustav.city)
        self.assertEqual('gustav@hofoper.at', gustav.email)
        self.assertEqual('NL', gustav.country)  # Country was not present in LDAP so will be set to NL always
        self.assertEqual('1111XX', gustav.postal_code)
        self.assertEqual('en-us', gustav.preferred_language)
        self.assertEqual('Eine Strasse 1', gustav.street)
        self.assertEqual('+43654365434680', gustav.phone_number)

        # Check group membership
        self.assertEqual(1, gustav.groups.count())
        membership = GroupMembership.objects.first()  # type: GroupMembership
        self.assertEqual(datetime(2010, 1, 1, tzinfo=timezone.utc), membership.start)
        self.assertIsNone(membership.end)

    def test_complete_group(self):
        """Test a group with all attributes."""
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
            },
            'uid=test2,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test2'],
            },
            'cn=A group,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['A group'],
                'description': ['Pianists play too much notes.'],
                'member': ['uid=test,ou=people,dc=esmgquadrivium,dc=nl',
                           'uid=test2,ou=people,dc=esmgquadrivium,dc=nl'],
                'mail': ['pianists@esmgquadrivium.nl'],
                'owner': ['uid=test,ou=people,dc=esmgquadrivium,dc=nl'],
            }
        }
        clone(entries)

        # Check row counts
        self.assertEqual(2, Person.objects.count())
        self.assertEqual(2, QGroup.objects.count())  # Includes 'current members' group
        self.assertEqual(2, GroupMembership.objects.count())

        # Check values
        p1 = Person.objects.get(username='test')
        # p2 = Person.objects.get(username='test2')
        group = QGroup.objects.get(email='pianists@esmgquadrivium.nl')
        self.assertEqual('A group', group.name)
        self.assertEqual('Pianists play too much notes.', group.description)
        self.assertEqual(p1, group.owner)
        self.assertEqual(2, group.user_set.count())  # 2 group members

    def test_invalid_member(self):
        """Group member with invalid DN should throw an error."""
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
            },
            'cn=agroup,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['agroup'],
                'member': ['uid=wronguid,ou=people,dc=esmgquadrivium,dc=nl'],
            }
        }
        with self.assertRaises(CloneError):
            clone(entries)

    def test_link_attribute_update(self):
        """Test the return value of the clone function."""
        entries = {
            'cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {'cn': ['Huidige leden']},
            'cn=agroup,ou=groups,dc=esmgquadrivium,dc=nl': {'cn': ['agroup']},
            'uid=aperson,ou=people,dc=esmgquadrivium,dc=nl': {'uid': ['aperson']},
        }
        actual = clone(entries, link_attribute='linkID')
        person_id = Person.objects.first().id
        group1_id = QGroup.objects.get(name='Huidige leden').id
        group2_id = QGroup.objects.get(~Q(name='Huidige leden')).id

        expect = [ModifyOperation('uid=aperson,ou=people,dc=esmgquadrivium,dc=nl', 'linkID', [person_id]),
                  ModifyOperation('cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl', 'linkID', [group1_id]),
                  ModifyOperation('cn=agroup,ou=groups,dc=esmgquadrivium,dc=nl', 'linkID', [group2_id])]
        self.assertCountEqual(expect, actual)
