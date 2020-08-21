"""Test cases for models.py."""
from django.test import TestCase

from activities.models import Activity


class ActivityTestCase(TestCase):
    """Test cases for activities"""
    a = Activity.objects.create(name='Testing activities')
    pass

