from django.test import TestCase

from sync.ldapoperations import ModifyDNOperation


class ModifyDNOperationTestCase(TestCase):

    def test_get_modify_dn_args(self):
        op = ModifyDNOperation("cn=hi,dc=example,dc=com", "cn=bye,dc=example,dc=com")
        dn, relative_dn, new_superior = op._get_modify_dn_args()
        self.assertEqual("cn=hi,dc=example,dc=com", dn)
        self.assertEqual("cn=bye", relative_dn)
        self.assertIs(None, new_superior)

    def test_get_modify_dn_args_new_superior(self):
        op = ModifyDNOperation("cn=hi,dc=example,dc=com", "cn=bye,dc=gone,dc=com")
        dn, relative_dn, new_superior = op._get_modify_dn_args()
        self.assertEqual("cn=hi,dc=example,dc=com", dn)
        self.assertEqual("cn=bye", relative_dn)
        self.assertEqual("dc=gone,dc=com", new_superior)

    def test_get_modify_dn_args_case_insensitive(self):
        op = ModifyDNOperation("cn=hi,dc=ExAmPlE,dc=com", "cn=bye,dc=example,dc=com")
        dn, relative_dn, new_superior = op._get_modify_dn_args()
        self.assertEqual("cn=hi,dc=ExAmPlE,dc=com", dn)
        self.assertEqual("cn=bye", relative_dn)
        self.assertIs(new_superior, None)
