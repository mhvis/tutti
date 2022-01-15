from decimal import Decimal

from django.test import TestCase

from members.models import Person, QGroup
from pennotools.contributie.process import get_contribution_fee, ContributionExemption

ONE = Decimal("1")
TWO = Decimal("2")
THREE = Decimal("3")
FOUR = Decimal("4")


class ContributionFeeTestCase(TestCase):
    """Tests get_contribution_fee()."""

    def test_student(self):
        p = Person.objects.create(username="me", is_student=True)
        fee = get_contribution_fee(p, ONE, TWO, [])
        self.assertEqual(ONE, fee)

    def test_non_student(self):
        p = Person.objects.create(username="me", is_student=False)
        fee = get_contribution_fee(p, ONE, TWO, [])
        self.assertEqual(TWO, fee)

    def test_exception(self):
        """Tests that an exception is applied to a group member."""
        p = Person.objects.create(username="me", is_student=True)
        g = QGroup.objects.create(name="A group")
        p.groups.add(g)
        exception = ContributionExemption(group=g, student=ONE, non_student=TWO)
        fee = get_contribution_fee(p, THREE, FOUR, [exception])
        self.assertEqual(ONE, fee)

    def test_no_exception(self):
        """Tests that an exception is not applied to non group members."""
        p = Person.objects.create(username="me", is_student=True)
        g = QGroup.objects.create(name="A group")
        # Not adding p to group
        exception = ContributionExemption(group=g, student=ONE, non_student=TWO)
        fee = get_contribution_fee(p, THREE, FOUR, [exception])
        self.assertEqual(THREE, fee)

    def test_multiple_exceptions(self):
        """Tests that the minimum value gets applied for multiple exceptions."""
        p = Person.objects.create(username="me", is_student=True)
        g1 = QGroup.objects.create(name="A group")
        g2 = QGroup.objects.create(name="Another group")
        p.groups.add(g1, g2)
        exceptions = [
            ContributionExemption(group=g1, student=FOUR, non_student=ONE),
            ContributionExemption(group=g2, student=THREE, non_student=ONE),
        ]
        fee = get_contribution_fee(p, TWO, ONE, exceptions)
        self.assertEqual(THREE, fee)
