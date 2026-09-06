from datetime import date
from unittest.mock import Mock, patch

from django.conf import settings
from django.test import TestCase, override_settings
from requests import HTTPError

from sync.aad.graph import Graph, GraphGroup, GraphUser
from sync.aad.operations import CreateUserOperation, TEMPORARY_ORPHAN_RECOVERY_DATE


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
    def test_create_user_includes_extension(self, request):
        response = Mock()
        response.json.return_value = {'id': 'user-id'}
        request.return_value = response
        graph = Graph('tenant', 'client-id', 'client-secret')
        graph.get_access_token = Mock(return_value='token')
        user = GraphUser('Test User', 'Test', 'test', 'en-US', 'User', 'test@example.com', 'immutable-id',
                         extension={'tuttiId': 1})

        graph.create_user(user)

        body = request.call_args.kwargs['json']
        self.assertEqual([{
            '@odata.type': 'microsoft.graph.openTypeExtension',
            'extensionName': 'nl.esmgquadrivium.tutti',
            'tuttiId': 1,
        }], body['extensions'])

    @override_settings(GRAPH_LICENSE_SKU_ID=None)
    @patch('sync.aad.operations.timezone.localdate', return_value=TEMPORARY_ORPHAN_RECOVERY_DATE)
    def test_create_user_operation_adopts_existing_user_without_extension(self, localdate):
        graph = Mock()
        graph.create_user.side_effect = HTTPError('400 Client Error')
        graph.get_user_by_immutable_id.return_value = GraphUser(
            'Test User', 'Test', 'test', 'en-US', 'User', 'test@example.com', 'immutable-id',
            directory_id='existing-user-id')
        user = GraphUser('Test User', 'Test', 'test', 'en-US', 'User', 'test@example.com', 'immutable-id',
                         extension={'tuttiId': 1})

        CreateUserOperation(user).apply(graph)

        graph.add_user_extension.assert_called_once_with('existing-user-id', {'tuttiId': 1})

    @override_settings(GRAPH_LICENSE_SKU_ID=None)
    @patch('sync.aad.operations.timezone.localdate', return_value=date(2026, 9, 7))
    def test_create_user_operation_does_not_adopt_user_after_recovery_date(self, localdate):
        graph = Mock()
        graph.create_user.side_effect = HTTPError('400 Client Error')
        user = GraphUser('Test User', 'Test', 'test', 'en-US', 'User', 'test@example.com', 'immutable-id',
                         extension={'tuttiId': 1})

        with self.assertRaisesRegex(HTTPError, '400 Client Error'):
            CreateUserOperation(user).apply(graph)

        graph.get_user_by_immutable_id.assert_not_called()


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
        user = GraphUser("Random Person", "Random", "testcase", "en-us", "Person", "testcase@esmgquadrivium.nl",
                         'asdf', extension={'Hello': "World"})

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
            group = GraphGroup("Group for a test case.", "Test Group", 'testgroup', extension={'hello': 'world'})
            group_id = self.graph.create_group(group)
            # Skip checking the created group (could add)
            self.graph.update_group(group_id, {'displayName': "Test Group 2"})
            self.graph.delete_group(group_id)
        except HTTPError as e:
            print(e.response.text)
            raise e
