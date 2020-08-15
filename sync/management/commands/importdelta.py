"""TEMPORARY: for importing deltas.json."""
import json
import sys
from argparse import ArgumentParser
from datetime import datetime, timezone
from typing import List

from django.core.management import BaseCommand
from django.db import transaction

from members.models import QGroup, Person, GroupMembership


class Command(BaseCommand):

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('--match', action='store_true')
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):  # noqa: C901
        # Parse JSON and convert to Django ORM objects
        a = json.load(sys.stdin)
        b = []
        for o in a.values():
            # Get Django group
            try:
                group = QGroup.objects.get(name=o['name'])
            except QGroup.DoesNotExist:
                self.stderr.write('Group not found: {}'.format(o['name']))
                continue

            def convert_people(uids: List[str]) -> List[Person]:
                people = []
                for uid in uids:
                    try:
                        people.append(Person.objects.get(username=uid))
                    except Person.DoesNotExist:
                        self.stderr.write('Person not found: {}'.format(uid))
                        continue
                return people

            # Convert start members
            start_members = convert_people(o['start_members'])

            # Convert delta people
            deltas = []
            for delta in o['deltas']:
                deltas.append({
                    'date': datetime.fromisoformat(delta['date']),
                    'added': convert_people(delta['added']),
                    'removed': convert_people(delta['removed']),
                })

            b.append({
                'group': group,
                'start_date': datetime.fromisoformat(o['start_date']),
                'start_members': start_members,
                'deltas': deltas
            })

        # print(json.dumps(b, indent=4, default=str))

        if not options.get('match'):
            self.stdout.write('Not matching group memberships, add --match')
            return

        # Create group memberships from the object
        c = []
        for o in b:
            # Create group memberships, start with start_members
            current = {p: GroupMembership(group=o['group'], user=p, start=o['start_date']) for p in o['start_members']}
            result = []

            # Walk over delta
            for oo in o['deltas']:
                for p in oo['added']:
                    if p in current:
                        raise KeyError('Person {} is already a member of {}'.format(p, o['group']))
                    current[p] = GroupMembership(group=o['group'], user=p, start=oo['date'])
                for p in oo['removed']:
                    m = current.pop(p)
                    m.end = oo['date']
                    result.append(m)

            # Copy remaining memberships
            for m in current.values():
                result.append(m)
            c.append({
                'group': o['group'],
                'memberships': result,
            })
        # print(json.dumps(c, indent=4, default=str))

        # Connect the new group memberships with existing database entries
        d = []
        for o in c:
            # Gather memberships in the database on March 30 2020
            saved_memberships = o['group'].groupmembership_set.filter(start__year=2020, start__month=3, start__day=30)
            for m in o['memberships']:  # type: GroupMembership
                if m.end:
                    # Do not connect memberships that don't need to be connected
                    d.append(m)
                    continue
                # Find connected membership
                connected = None
                for m2 in saved_memberships:
                    if m.user.id == m2.user.id:
                        connected = m2
                        break
                if not connected:
                    # When no connection found, assume membership ended around March 29, 2020
                    m.end = datetime(2020, 3, 29, 12, 0, tzinfo=timezone.utc)
                    d.append(m)
                else:
                    # Else connected the linked memberships
                    connected.start = m.start
                    d.append(connected)

        print(json.dumps(d, indent=4, default=str), file=self.stdout)

        if not options.get('apply'):
            self.stdout.write("Not applying, add --apply after creating a backup")
            return

        with transaction.atomic():
            for m in d:
                m.save()
