"""Test cases for models.py."""
from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from activities.models import Activity


class ActivityTestCase(TestCase):
    """Test cases for activities."""

    def test_is_closed(self):
        """Tests is_closed with start_date and closing_date."""
        # For convenience I've put this in one testcase but these are actually separate tests
        far_ahead = datetime(2123, 1, 1, tzinfo=timezone.utc)
        way_back = datetime(1123, 1, 1, tzinfo=timezone.utc)
        # Start date not closed
        a = Activity.objects.create(name='Test', start_date=far_ahead)
        self.assertFalse(a.is_closed)
        # Start date closed
        a = Activity.objects.create(name='Test', start_date=way_back)
        self.assertTrue(a.is_closed)
        # Closed date not closed
        a = Activity.objects.create(name='Test', start_date=far_ahead, closing_date=far_ahead)
        self.assertFalse(a.is_closed)
        # Closed date closed
        a = Activity.objects.create(name='Test', start_date=far_ahead, closing_date=way_back)
        self.assertTrue(a.is_closed)
