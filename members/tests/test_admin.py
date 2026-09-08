"""Test cases for the members admin."""

from django.test import TestCase
from django.urls import reverse

from members.models import Person, QGroup


class PersonAdminTestCase(TestCase):
    """Test cases for the person admin."""

    def test_changelist_accepts_member_filter_and_search(self):
        """The member filter can be combined with a search query."""
        members_group = QGroup.objects.create(name="Members")
        administrator = Person.objects.create_superuser(
            username="administrator",
            email="administrator@example.com",
            password="password",
        )
        self.client.force_login(administrator)

        with self.settings(MEMBERS_GROUP=members_group.pk):
            response = self.client.get(
                reverse("admin:members_person_changelist"),
                {"is_member": "no", "q": "rue"},
            )

        self.assertEqual(response.status_code, 200)
