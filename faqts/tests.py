from django.conf import settings
from django.test import TestCase

from faqts.facts import instrument_counts
from members.models import Person, QGroup, Instrument


class FactsTestCase(TestCase):
    """Test case for facts.py."""

    def test_instrument_counts(self):
        """Tests that only members are included in the instruments summary."""
        # Create group
        members_group = QGroup.objects.create(name="Members")
        # Create people
        member1 = Person.objects.create(username="member1", first_name="Member 1")
        member2 = Person.objects.create(username="member2", first_name="Member 2")
        non_member = Person.objects.create(username="not_a_member", first_name="Not A Member")
        # Set group memberships
        member1.groups.add(members_group)
        member2.groups.add(members_group)
        # Create instruments
        violin = Instrument.objects.create(name="Violin")
        piano = Instrument.objects.create(name="Piano")
        # Link instruments with people
        member1.instruments.add(violin, piano)
        member2.instruments.add(violin)
        non_member.instruments.add(violin)
        # Set members group
        settings.MEMBERS_GROUP = members_group.id

        # Test result
        result = instrument_counts()
        # Piano will be the first result because it is sorted alphabetically
        self.assertEqual(1, result[0][1])  # No of piano
        self.assertEqual(2, result[1][1])  # No of violin
