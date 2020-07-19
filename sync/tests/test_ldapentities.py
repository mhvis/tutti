from django.test import TestCase

from sync.ldapentities import LDAPGroup
from members.models import Person, QGroup


class ModelsTestCase(TestCase):
    def test_group_membership_current(self):
        """Test group membership is included in member list."""
        p = Person.objects.create(username='test')
        g = QGroup.objects.create(name='group')
        p.groups.add(g)
        ldap_attrs = LDAPGroup(QGroup.objects.first()).get_attributes()
        self.assertEqual(['uid=test,ou=people,dc=esmgquadrivium,dc=nl'], ldap_attrs['member'])

    def test_no_group_membership(self):
        """Test not a group member."""
        Person.objects.create(username='test')
        QGroup.objects.create(name='group')
        ldap_attrs = LDAPGroup(QGroup.objects.first()).get_attributes()
        self.assertNotIn('member', ldap_attrs)
