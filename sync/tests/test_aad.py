from django.conf import settings
from django.test import TestCase
from requests import HTTPError

from sync.aad.graph import Graph, GraphUser, GraphGroup


class AADTestCase(TestCase):
    """Some test cases for Azure Active Directory.

    The test cases are supposed to clean up after themselves on Azure, but they
    may leave artifacts if they fail.
    """

    def setUp(self):
        if not settings.GRAPH_CLIENT_ID:
            self.skipTest("Microsoft Graph is not set up")
            return
        self.graph = Graph.from_settings()
        self.graph.extension_id = "nl.esmgquadrivium.tutti-test"

    def test_user(self):
        """Tests user creation, update, license, extension and deletion."""
        user = GraphUser("Random Person", "Random", "testcase", "en-us", "Person", "testcase@esmgquadrivium.nl", 'asdf')

        def get_user(graph: Graph, user_id: str):
            # Get user
            fields = ['id', 'displayName', 'userPrincipalName', 'identities',
                      'lastPasswordChangeDateTime', 'licenseAssignmentStates',
                      'passwordPolicies',
                      'passwordProfile', 'usageLocation', 'onPremisesImmutableId']
            params = {'$select': ','.join(fields), '$expand': 'extensions'}
            return graph.call_resource('users/{}'.format(user_id), params=params).json()

        try:
            # Create user
            user_id = self.graph.create_user(user)
            # Add extension data
            self.graph.add_user_extension(user_id, {'Hello': "World"})
            # Assign Office 365 license (without Exchange)
            self.graph.assign_license(user_id=user_id,
                                      sku_id='6634e0ce-1a9f-428c-a498-f84ec7b8aa2e',
                                      disabled_plans=['9aaf7827-d63c-4b61-89c3-182f06f82e5c'])

            # Get user and check if all fields are set
            user = get_user(self.graph, user_id)
            # print(json.dumps(user, indent=4))
            self.assertEqual('testcase@esmgquadrivium.nl', user['userPrincipalName'])
            self.assertEqual('asdf', user['onPremisesImmutableId'])
            # Assert license
            self.assertEqual('6634e0ce-1a9f-428c-a498-f84ec7b8aa2e',
                             user['licenseAssignmentStates'][0]['skuId'])
            self.assertEqual('9aaf7827-d63c-4b61-89c3-182f06f82e5c',
                             user['licenseAssignmentStates'][0]['disabledPlans'][0])
            # Assert extension
            self.assertEqual("World", user['extensions'][0]['Hello'])

            # Update user
            self.graph.update_user(user_id, {'displayName': "Different Name"})
            # Check if updated
            user = get_user(self.graph, user_id)
            self.assertEqual("Different Name", user['displayName'])

            # Delete
            self.graph.delete_user(user_id)
        except HTTPError as e:
            print(e.response.text)
            raise e

    def test_group(self):
        """Tests group creation and deletion, but not membership add/delete."""
        try:
            group = GraphGroup("Group for a test case.", "Test Group", 'testgroup')
            group_id = self.graph.create_group(group)
            self.graph.add_group_extension(group_id, {'hello': 'world'})
            # Skip checking the created group (could add)
            self.graph.update_group(group_id, {'displayName': "Test Group 2"})
            self.graph.delete_group(group_id)
        except HTTPError as e:
            print(e.response.text)
            raise e
