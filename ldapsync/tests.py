from django.test import TestCase


class CloneTestCase(TestCase):

    def test_data_issues(self):
        # Issues that need to be detected:
        # * givenName/sn that differs from cn
        # * qAzureUPN that differs from uid
        # * Multi-valued attributes
        # ....
        pass

    pass


class SyncTestCase(TestCase):
    """Test one-way sync of two datasets."""
    pass
