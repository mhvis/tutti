from datetime import date

from django.test import TestCase

from ldapsync.clone import CloneError, clone
from ldapsync.ldapoperations import AddOperation, DeleteOperation, ModifyDNOperation, ModifyOperation
from ldapsync.sync import sync
from qluis.models import Person, QGroup


class CloneTestCase(TestCase):
    def setUp(self) -> None:
        pass

    def test_minimal(self):
        """Cloning should work for minimal entry."""
        entries = {
            'uid=aperson,ou=people,dc=esmgquadrivium,dc=nl': {'uid': ['aperson']},
            'cn=agroup,ou=groups,dc=esmgquadrivium,dc=nl': {'cn': ['agroup']},
        }
        clone(entries)
        self.assertEqual(1, Person.objects.all().count())
        self.assertEqual(1, QGroup.objects.all().count())
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
        # TODO
        pass

    def test_date_of_birth(self):
        """Test conversion of date of birth."""
        entries = {'uid=test,ou=people,dc=esmgquadrivium,dc=nl': {
            'uid': ['test'],
            'qDateOfBirth': ['19951226'],
        }}
        clone(entries)
        self.assertEqual(date(1995, 12, 26), Person.objects.first().date_of_birth)

    def test_member_start_end(self):
        """Test conversion of qMemberStart/qMemberEnd to group membership."""
        # TODO
        pass

    def test_group_membership(self):
        """Test group membership conversion."""
        # TODO
        pass

    def test_full_person(self):
        """Test a person with (almost) all attributes."""
        # TODO
        pass

    def test_complete_group(self):
        """Test a group with all attributes."""
        # TODO
        pass

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
