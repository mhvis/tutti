from datetime import date, datetime

from django.test import TestCase

from ldapsync.clone import CloneError, clone
from ldapsync.ldapoperations import AddOperation, DeleteOperation, ModifyDNOperation, ModifyOperation
from ldapsync.sync import sync
from qluis.models import Person, QGroup, ExternalCard, ExternalCardLoan, Membership, Instrument, GSuiteAccount, Key


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
        self.assertEqual(0, Membership.objects.count())
        self.assertEqual('aperson', Person.objects.first().username)
        self.assertEqual('agroup', QGroup.objects.first().name)

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
        self.assertEqual('y', loan.deposit_made)
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
            'cn=Huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['Huidige leden'],
                'member': ['uid=test,ou=people,dc=esmgquadrivium,dc=nl'],
            }
        }
        with self.assertRaises(CloneError):
            clone(entries)

        # Has no qMemberStart+qMemberEnd, so should not be in current members group
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
            },
            'cn=Huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {
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
            'cn=Huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {
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
                'qMemberStart': [datetime(2010, 2, 2)],
                'qMemberEnd': [datetime(2010, 5, 2)],
            },
            'cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['Huidige leden'],
                'member': [],
            }
        }
        clone(entries)
        self.assertEqual(1, Person.objects.count())
        self.assertEqual(1, QGroup.objects.count())
        self.assertEqual(1, Membership.objects.count())
        membership = Membership.objects.first()
        self.assertEqual(datetime(2010, 2, 2), membership.start)
        self.assertEqual(datetime(2010, 5, 2), membership.end)

    def test_member_start(self):
        """Test conversion of a current member with only qMemberStart to group membership."""
        entries = {
            'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
                'uid': ['test'],
                'qMemberStart': [datetime(2010, 2, 2)],
            },
            'cn=huidige leden,ou=groups,dc=esmgquadrivium,dc=nl': {
                'cn': ['Huidige leden'],
                'member': ['uid=test,ou=people,dc=esmgquadrivium,dc=nl'],
            }
        }
        clone(entries)
        self.assertEqual(1, QGroup.objects.count())
        self.assertEqual(1, Person.objects.count())
        self.assertEqual(1, Membership.objects.count())
        membership = Membership.objects.first()
        self.assertEqual(datetime(2010, 2, 2), membership.start)
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
        self.assertEqual(1, QGroup.objects.count())
        self.assertEqual(1, Person.objects.count())
        self.assertEqual(1, Membership.objects.count())
        membership = Membership.objects.first()
        self.assertIsNone(membership.end)

    def test_full_person(self):
        """Test a person with (almost) all attributes."""
        entries = {
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
                'qInstrumentVoice': ['Piano', 'Conducting'],
                'qIsStudent': [True],
                'qKeyAccess': [15, 27],
                'qKeyWatcherID': [1234],
                'qKeyWatcherPIN': [5678],
                'qMemberStart': [datetime(2010, 1, 1)],
                'qSEPADirectDebit': [True],
                'initials': 'G.',
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
        self.assertEqual(1, Membership.objects.count())
        # Check the values
        gustav = Person.objects.first()  # type: Person
        self.assertEqual('gustav', gustav.username)
        self.assertEqual('Gustav', gustav.first_name)
        self.assertEqual('Mahler', gustav.last_name)
        self.assertEqual(datetime(2020, 1, 1), gustav.bhv_certificate)
        self.assertEqual(1234567, gustav.tue_card_number)
        self.assertEqual(date(1860, 7, 7), gustav.date_of_birth)
        self.assertEqual('Alma', gustav.field_of_study)
        self.assertCountEqual(['gustav@esmgquadrivium.nl', 'mahler@esmgquadrivium.nl'],
                              [a.email for a in gustav.gsuite_accounts.all()])
        self.assertEqual('Male', gustav.gender)
        self.assertEqual('NL45ABNA9574218201', gustav.iban)
        self.assertEqual('GUSMAL', gustav.person_id)
        self.assertCountEqual(['Piano', 'Conducting'],
                              [i.name for i in gustav.instruments.all()])
        self.assertTrue(gustav.is_student)
        self.assertCountEqual([15, 27],
                              [k.number for k in gustav.key_access.all()])
        self.assertEqual(1234, gustav.keywatcher_id)
        self.assertEqual(5678, gustav.keywatcher_pin)
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
        membership = Membership.objects.first()  # type: Membership
        self.assertEqual(datetime(2010, 1, 1), membership.start)
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
        self.assertEqual(2, Membership.objects.count())

        # Check values
        p1 = Person.objects.get(username='test')
        # p2 = Person.objects.get(username='test2')
        group = QGroup.objects.get(email='pianists@esmgquadrivium.nl')
        self.assertEqual('A group', group.name)
        self.assertEqual('Pianists play too much notes.', group.description)
        self.assertEqual(p1, group.owner)

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
            'uid=aperson,ou=people,dc=esmgquadrivium,dc=nl': {'uid': ['aperson']},
            'cn=agroup,ou=groups,dc=esmgquadrivium,dc=nl': {'cn': ['agroup']},
        }
        actual = clone(entries, link_attribute='linkID')
        person_id = Person.objects.first().id
        group_id = QGroup.objects.first().id
        expect = [ModifyOperation('uid=aperson,ou=people,dc=esmgquadrivium,dc=nl', 'linkID', [str(person_id)]),
                  ModifyOperation('cn=agroup,ou=groups,dc=esmgquadrivium,dc=nl', 'linkID', [str(group_id)])]
        self.assertCountEqual(expect, actual)


class SyncTestCase(TestCase):
    """Test one-way sync of two datasets."""

    def test_none(self):
        """No operations need to be performed."""
        source = {'uid=peep': {'uid': ['peep'], 'name': ['Henk'], 'id': ['4']}}
        target = {'uid=peep': {'uid': ['peep'], 'name': ['Henk'], 'id': ['4']}}
        operations = sync(source, target, on='id')
        self.assertEqual([], operations)

    def test_add(self):
        source = {'uid=test': {'uid': ['test'], 'id': ['4']}}
        target = {}
        operations = sync(source, target, on='id')
        expect = [AddOperation('uid=test', {'uid': ['test'], 'id': ['4']})]
        self.assertEqual(expect, operations)

    def test_delete(self):
        source = {}
        target = {'uid=test': {'uid': ['test'], 'id': ['4']}}
        operations = sync(source, target, on='id')
        self.assertEqual([DeleteOperation('uid=test')], operations)

    def test_modify(self):
        source = {'uid=test': {'uid': ['test'], 'name': ['Piet'], 'id': ['4']}}
        target = {'uid=test': {'uid': ['test'], 'name': ['Henk'], 'id': ['4']}}
        operations = sync(source, target, on='id')
        self.assertEqual([ModifyOperation('uid=test', 'name', ['Piet'])], operations)

    def test_modify_dn(self):
        source = {'uid=test': {'uid': ['hmm'], 'id': ['4']}}
        target = {'uid=test2': {'uid': ['hmm'], 'id': ['4']}}
        operations = sync(source, target, on='id')
        self.assertEqual([ModifyDNOperation('uid=test', 'uid=test2')], operations)
