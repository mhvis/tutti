from django.core.management import BaseCommand
from requests import HTTPError

from sync.aad.graph import Graph
from sync.aad.operations import DeleteUserOperation, DeleteGroupOperation
from sync.aad.sync import aad_sync_objects, aad_sync_members


def handle_operations(operations, graph, out):
    """Prints operations to out, asks for confirmation and applies."""
    if not operations:
        out.write('No operations to apply')
        return
    for o in operations:
        out.write(str(o))
    y = input('Apply operations? [y/N] ')
    if y != 'y':
        out.write('Applying operations skipped')
    else:
        out.write('Applying operations...')
        for o in operations:
            o.apply(graph)


class Command(BaseCommand):
    help = "Interactively sync users and groups with Azure Active Directory. Does only one-way sync to Azure."

    def handle(self, *args, **options):
        try:
            graph = Graph.from_settings()

            self.stdout.write('Comparing user and group objects...')
            operations = aad_sync_objects(graph)

            # Split out delete operations
            delete_ops = []
            non_delete_ops = []
            for o in operations:
                if isinstance(o, DeleteUserOperation) or isinstance(o, DeleteGroupOperation):
                    delete_ops.append(o)
                else:
                    non_delete_ops.append(o)

            self.stdout.write('Create and update operations:')
            handle_operations(non_delete_ops, graph, self.stdout)
            self.stdout.write('Delete operations:')
            handle_operations(delete_ops, graph, self.stdout)

            self.stdout.write("Comparing group memberships...")
            operations = aad_sync_members(graph)
            self.stdout.write("Group membership operations:")
            handle_operations(operations, graph, self.stdout)

            # Do a sanity check for possible licensing issues
            self.stdout.write("Checking licenses...")
            users = graph.get_paged("users", params={"$select": "userPrincipalName,assignedLicenses"})
            without_license = [u for u in users if not u.get("assignedLicenses")]
            for u in without_license:
                self.stdout.write("User {} has no assigned licenses!".format(u["userPrincipalName"]))

            # Print orphans
            self.stdout.write("Checking extensions...")
            users = graph.get_paged("users", params={"$select": "userPrincipalName", "$expand": "extensions"})
            groups = graph.get_paged("groups", params={"$select": "displayName", "$expand": "extensions"})
            for o in users + groups:
                ext = o.get("extensions")
                if not ext or len(ext) != 1 or ext[0]["id"] != "nl.esmgquadrivium.tutti":
                    self.stdout.write("Unexpected extension for object: {}".format(o))
        except HTTPError as e:
            self.stderr.write(str(e))
            self.stderr.write(str(e.response.json()))
