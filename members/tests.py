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
