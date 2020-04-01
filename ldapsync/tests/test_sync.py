from django.test import TestCase

from ldapsync.ldapoperations import AddOperation, DeleteOperation, ModifyDNOperation, ModifyOperation
from ldapsync.sync import sync


class SyncTestCase(TestCase):
    """Test one-way sync of two datasets."""

    def test_none(self):
        """No operations need to be performed."""
        source = {'uid=peep': {'uid': ['peep'], 'name': ['Henk'], 'id': [4]}}
        target = {'uid=peep': {'uid': ['peep'], 'name': ['Henk'], 'id': [4]}}
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
        change_to = {'uid=test': {'uid': ['test'], 'name': ['Piet'], 'id': ['4']}}
        to_change = {'uid=test': {'uid': ['test'], 'name': ['Henk'], 'id': ['4']}}
        operations = sync(change_to, to_change, on='id')
        self.assertEqual([ModifyOperation('uid=test', 'name', ['Piet'])], operations)

    def test_modify_empty_missing1(self):
        change_to = {'uid=test': {'uid': ['test'], 'name': [], 'id': ['4']}}
        to_change = {'uid=test': {'uid': ['test'], 'id': ['4']}}
        operations = sync(change_to, to_change, on='id')
        self.assertEqual([], operations)

    # This is currently not supported
    # def test_modify_empty_missing2(self):
    #     change_to = {'uid=test': {'uid': ['test'], 'id': ['4']}}
    #     to_change = {'uid=test': {'uid': ['test'], 'name': [], 'id': ['4']}}
    #     operations = sync(change_to, to_change, on='id')
    #     self.assertEqual([], operations)

    def test_modify_list(self):
        change_to = {'uid=test': {'uid': ['test'], 'name': ['Piet', 'Henk'], 'id': [4]}}
        to_change = {'uid=test': {'uid': ['test'], 'name': ['Piet'], 'id': [4]}}
        operations = sync(change_to, to_change, on='id')
        self.assertEqual([ModifyOperation('uid=test', 'name', ['Piet', 'Henk'])], operations)

    def test_modify_list2(self):
        source = {'uid=test': {'uid': ['test'], 'name': ['Henk', 'Piet'], 'id': [4]}}
        target = {'uid=test': {'uid': ['test'], 'name': ['Piet', 'Henk'], 'id': [4]}}
        operations = sync(source, target, on='id')
        self.assertEqual([], operations)

    def test_modify_dn(self):
        change_to = {'uid=test': {'id': ['4']}}
        to_change = {'uid=test2': {'id': ['4']}}
        operations = sync(change_to, to_change, on='id')
        self.assertEqual([ModifyDNOperation('uid=test2', 'uid=test')], operations)

    def test_modify_dn_attribute(self):
        change_to = {'uid=test': {'uid': ['test'], 'id': ['4']}}
        to_change = {'uid=test2': {'uid': ['test2'], 'id': ['4']}}
        operations = sync(change_to, to_change, on='id')
        # ModifyDNOperation should be before ModifyOperation
        self.assertEqual([ModifyDNOperation('uid=test2', 'uid=test'),
                          ModifyOperation('uid=test', 'uid', ['test'])], operations)

    def test_entry_without_matching_attribute(self):
        change_to = {'uid=test': {'uid': ['test'], 'id': [1]}}
        to_change1 = {'uid=test': {'uid': ['test']}}
        to_change2 = {'uid=test': {'uid': ['test'], 'id': []}}
        operations1 = sync(change_to, to_change1, on='id')
        operations2 = sync(change_to, to_change2, on='id')
        expect = [DeleteOperation('uid=test'), AddOperation('uid=test', {'uid': ['test'], 'id': [1]})]
        self.assertEqual(expect, operations1)
        self.assertEqual(expect, operations2)
