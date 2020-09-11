"""TEMPORARY! For cloning Azure onPremisesImmutableId."""
from django.core.management import BaseCommand
from requests import HTTPError

from members.models import Person
from sync.aad.graph import Graph


class Command(BaseCommand):
    help = "Clone Azure onPremisesImmutableId property."

    def handle(self, *args, **options):
        try:
            graph = Graph.from_settings()

            # Get all users with immutable ID
            params = {
                '$select': 'id,userPrincipalName,onPremisesImmutableId',
                '$expand': 'extensions($filter=id eq \'nl.esmgquadrivium.tutti\')',
            }
            objects = graph.get_paged('users', params=params)
            for o in objects:
                self.stdout.write('Object: {}'.format(o))
                pk = o['extensions'][0]['tuttiId']
                self.stdout.write('Setting immutable ID of {} ({}) to {}'.format(o['userPrincipalName'],
                                                                                 pk,
                                                                                 o['onPremisesImmutableId']))
                person = Person.objects.get(pk=pk)
                person.azure_immutable_id = o['onPremisesImmutableId']
                person.save()
        except HTTPError as e:
            self.stderr.write(str(e))
            self.stderr.write(str(e.response.json()))
