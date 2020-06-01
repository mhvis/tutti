import argparse
import json
from argparse import ArgumentParser
from difflib import ndiff

import msal
import requests
from django.core.management import BaseCommand

from members.models import Person, QGroup


class Command(BaseCommand):
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('params',
                            type=argparse.FileType('r'),
                            default='-',
                            help='JSON file with secret and authority endpoint.')

    def handle(self, *args, **options):
        config = json.load(options['params'])

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
        huidige_leden = QGroup.objects.get(pk=51)
        for group in QGroup.objects.all():
            peep_qs = Person.objects.filter(groups=huidige_leden).filter(groups=group)
            peeps = ['{}@esmgquadrivium.nl'.format(p.username) for p in peep_qs]
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
