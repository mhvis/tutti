from unittest.mock import Mock, patch

from django.conf import settings
from django.test import TestCase, override_settings
from requests import HTTPError

from sync.aad.graph import Graph, GraphGroup, GraphUser
from sync.aad.operations import CreateUserOperation, add_extension_with_retry


class GraphErrorTestCase(TestCase):
    @patch('sync.aad.graph.requests.request')
    def test_call_includes_graph_error_in_raised_exception(self, request):
        """Graph error details remain available to asynchronous task logs."""
        response = Mock()
        response.text = '{"error":{"code":"Request_BadRequest","message":"Invalid value"}}'
        response.raise_for_status.side_effect = HTTPError('400 Client Error', response=response)
        request.return_value = response
        graph = Graph('tenant', 'client-id', 'client-secret')
        graph.get_access_token = Mock(return_value='token')

        with self.assertRaisesRegex(HTTPError, 'Request_BadRequest') as context:
            graph.call('https://graph.microsoft.com/v1.0/users', method='POST')

        self.assertIs(context.exception.response, response)

    @patch('sync.aad.graph.requests.request')
    def test_create_user_does_not_include_extension(self, request):
        response = Mock()
        response.json.return_value = {'id': 'user-id'}
        request.return_value = response
        graph = Graph('tenant', 'client-id', 'client-secret')
        graph.get_access_token = Mock(return_value='token')
        user = GraphUser('Test User', 'Test', 'test', 'en-US', 'User', 'test@example.com', 'immutable-id',
                         extension={'tuttiId': 1})

        graph.create_user(user)

        body = request.call_args.kwargs['json']
        self.assertNotIn('extensions', body)

    @patch('sync.aad.operations.time.sleep')
    def test_add_extension_retries_404_with_exponential_backoff(self, sleep):
        graph = Mock()
        response = Mock(status_code=404)
        graph.add_extension.side_effect = [HTTPError('404 Client Error', response=response), None]

        add_extension_with_retry(graph, 'users/user-id/extensions', {'tuttiId': 1})

        self.assertEqual(2, graph.add_extension.call_count)
        sleep.assert_called_once_with(1)

    @override_settings(GRAPH_LICENSE_SKU_ID=None)
    def test_create_user_operation_restores_conflicting_deleted_user(self):
        response = Mock()
        response.json.return_value = {
            'error': {
                'details': [{
                    'code': 'ConflictingObjects',
                    'target': 'User_75f4c728-a149-4328-84e1-bde0875cacab',
                }],
            },
        }
        graph = Mock()
        graph.create_user.side_effect = HTTPError('400 Client Error', response=response)
        graph.get_deleted_user_immutable_id.return_value = 'immutable-id'
        graph.restore_deleted_user.return_value = '75f4c728-a149-4328-84e1-bde0875cacab'
        graph.get_user.return_value = GraphUser(
            'Test User', 'Test', 'test', 'en-US', 'User', 'test@example.com', 'immutable-id',
            directory_id='75f4c728-a149-4328-84e1-bde0875cacab', extension={'tuttiId': 1})
        user = GraphUser('Test User', 'Test', 'test', 'en-US', 'User', 'test@example.com', 'immutable-id',
                         extension={'tuttiId': 1})

        CreateUserOperation(user).apply(graph)

        graph.get_deleted_user_immutable_id.assert_called_once_with('75f4c728-a149-4328-84e1-bde0875cacab')
        graph.restore_deleted_user.assert_called_once_with('75f4c728-a149-4328-84e1-bde0875cacab')
        graph.get_user.assert_called_once_with('75f4c728-a149-4328-84e1-bde0875cacab')
        graph.add_extension.assert_not_called()

    @override_settings(GRAPH_LICENSE_SKU_ID=None)
    def test_create_user_operation_reraises_unidentified_conflict(self):
        graph = Mock()
        graph.create_user.side_effect = HTTPError('400 Client Error')
        user = GraphUser('Test User', 'Test', 'test', 'en-US', 'User', 'test@example.com', 'immutable-id',
                         extension={'tuttiId': 1})

        with self.assertRaisesRegex(HTTPError, '400 Client Error'):
            CreateUserOperation(user).apply(graph)

        graph.get_deleted_user_immutable_id.assert_not_called()
        graph.restore_deleted_user.assert_not_called()


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
