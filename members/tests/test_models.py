"""Test cases for models.py."""
from django.conf import settings
from django.test import TestCase

from members.models import QGroup, Person, GroupMembership


class GroupMembershipTestCase(TestCase):
    """Test cases for creation of historical records for group membership."""

    def test_add_remove(self):
        """Test group membership add and removal (should create history record)."""
        # Add
        g = QGroup.objects.create(name='Group')
        p = Person.objects.create(username='person')
        p.groups.add(g)
        self.assertEqual(1, GroupMembership.objects.count())
        membership = GroupMembership.objects.first()  # type: GroupMembership
        self.assertIsNone(membership.end)

        # Remove
        p.groups.remove(g)
        membership.refresh_from_db()
        self.assertIsNotNone(membership.end)


class PersonQuerySetTestCase(TestCase):
    def test_filter_members(self):
        """Tests filter_members()."""
        # Create group + member + non_member
        members_group = QGroup.objects.create(name="Members")
        member = Person.objects.create(username="a_member", first_name="A Member")
        member.groups.add(members_group)
        Person.objects.create(username="not_a_member", first_name="Not A Member")
        # Set members group
        settings.MEMBERS_GROUP = members_group.id
        # Test filter
        qs = Person.objects.filter_members()
        self.assertEqual(member, qs.first())
        self.assertEqual(1, qs.count())
