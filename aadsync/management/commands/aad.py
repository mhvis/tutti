import json
from argparse import ArgumentParser
from difflib import ndiff

import msal
import requests
from django.core.management import BaseCommand

from members.models import QGroup

"""
The configuration file would look like this (sans those // comments):
{
    "authority": "https://login.microsoftonline.com/Enter_the_Tenant_Name_Here",
    "client_id": "your_client_id",
    "scope": ["https://graph.microsoft.com/.default"],
        // For more information about scopes for an app, refer:
        // https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow#second-case-access-token-request-with-a-certificate"
    "secret": "The secret generated by AAD during your confidential app registration",
        // For information about generating client secret, refer:
        // https://github.com/AzureAD/microsoft-authentication-library-for-python/wiki/Client-Credentials#registering-client-secrets-using-the-application-registration-portal
}
"""


class Command(BaseCommand):
    def add_arguments(self, parser: ArgumentParser):
        pass
        parser.add_argument('params', help='JSON file with secret and authority endpoint.')

    def handle(self, *args, **options):
        config = json.load(open(options['params']))
        app = msal.ConfidentialClientApplication(config['client_id'],
                                                 authority=config['authority'],
                                                 client_credential=config['secret'])

        # Get token
        result = app.acquire_token_for_client(scopes=config['scope'])
        headers = {'Authorization': 'Bearer {}'.format(result['access_token'])}

        # Get AD data
        ad_groups = requests.get('https://graph.microsoft.com/v1.0/groups', headers=headers).json()['value']
        members_url = 'https://graph.microsoft.com/v1.0/groups/{}/members'
        lines = []
        for ad_group in ad_groups:
            m = requests.get(members_url.format(ad_group['id']), headers=headers).json()['value']
            m = [x['userPrincipalName'] for x in m]
            m.sort()
            m = '|'.join(m)
            lines.append('{}: {}'.format(ad_group['displayName'], m))
        lines.sort()
        ad_data = '\n'.join(lines)

        # Get Tutti data
        lines = []
        for group in QGroup.objects.all():
            peeps = ['{}@esmgquadrivium.nl'.format(p.username) for p in group.user_set.all()]
            peeps.sort()
            lines.append('{}: {}'.format(group.name, '|'.join(peeps)))
        lines.sort()
        tutti_data = '\n'.join(lines)

        print()
        print('# AD data')
        print()
        print(ad_data)
        print()
        print('# Tutti data')
        print()
        print(tutti_data)
        print()
        print('# Diff')
        print()
        diff = ndiff(ad_data.splitlines(keepends=True),
                     tutti_data.splitlines(keepends=True))
        print(''.join(diff), end="")
