"""AAD sync methods using the graph and operations modules."""
from typing import Dict, List, Tuple

from members.models import QGroup, Person
from sync.aad.graph import Graph, GraphGroup, GraphUser, GraphObject
from sync.aad.operations import SyncOperation, CreateUserOperation, DeleteUserOperation, UpdateUserOperation, \
    CreateGroupOperation, DeleteGroupOperation, UpdateGroupOperation, AddGroupMemberOperation, \
    RemoveGroupMemberOperation


def aad_sync_objects(graph: Graph) -> List[SyncOperation]:
    """Gets the sync operations for syncing users and groups with AAD.

    Group memberships are synced separately and needs to be done after the
    operations returned here have been applied.
    """
    operations = []
    # Sync users
    local_users = [convert_local_person(p) for p in Person.objects.filter(groups=51)]  # Todo: remove hardcoded filter
    aad_users = graph.get_users()
    operations.extend(sync_users(local_users, aad_users))
    # Sync groups
    local_groups = [convert_local_group(g) for g in QGroup.objects.all()]
    aad_groups = graph.get_groups()
    operations.extend(sync_groups(local_groups, aad_groups))
    return operations


def aad_sync_members(graph: Graph) -> List[SyncOperation]:
    """Gets the sync operation for group membership adds/deletes.

    This uses the remote groups as the groups that will be synced, so this must
    be run after the aad_sync_objects operations have been applied on AAD. This
    is because the remote groups need to have been created already in order to
    be able to sync group memberships.
    """
    operations = []
    aad_users = graph.get_users()
    local_id_map = {u.extension["tuttiId"]: u for u in aad_users}
    remote_id_map = {u.directory_id: u for u in aad_users}
    for group in graph.get_groups():
        # Get local and remote group members
        qs = Person.objects.filter(groups=group.extension["tuttiId"])
        # Here we silently ignore local people that don't have a remote account
        local = [local_id_map[p.id] for p in qs if p.id in local_id_map]
        remote = [remote_id_map[i] for i in graph.get_group_members(group.directory_id)]
        # Sync
        operations.extend(sync_members(group, local, remote))
    return operations


def convert_local_person(person: Person) -> GraphUser:
    """Converts a local Django person to a Graph object."""
    return GraphUser(person.get_full_name(),
                     person.first_name or None,  # Optional
                     person.username,
                     person.preferred_language or None,
                     person.last_name or None,
                     "{}@esmgquadrivium.nl".format(person.username),
                     extension={"tuttiId": person.id})


def convert_local_group(group: QGroup) -> GraphGroup:
    """Converts a local Django person to a Graph object."""
    # Strips non-alphanumeric characters and limits to 64 characters
    mail_nickname = "".join([c for c in group.name if c.isalnum()]).lower()[:64]
    return GraphGroup(group.description or None,  # Optional, if omitted it should be None
                      group.name,
                      mail_nickname,
                      extension={"tuttiId": group.id})


def sync_users(local: List[GraphUser], remote: List[GraphUser]) -> List[SyncOperation]:
    """Returns the necessary operations to sync the local and remote users."""
    operations = []
    # Create+delete users
    to_create, to_delete, remaining_pairs = get_create_delete(local, remote)
    operations.extend([CreateUserOperation(u) for u in to_create])
    operations.extend([DeleteUserOperation(u) for u in to_delete])
    # Updates
    operations.extend([UpdateUserOperation(u, c) for u, c in get_update_list(remaining_pairs)])
    return operations


def sync_groups(local: List[GraphGroup], remote: List[GraphGroup]) -> List[SyncOperation]:
    """Returns the necessary operations to sync the local and remote groups."""
    operations = []
    # Create+delete
    to_create, to_delete, remaining_pairs = get_create_delete(local, remote)
    operations.extend([CreateGroupOperation(g) for g in to_create])
    operations.extend([DeleteGroupOperation(g) for g in to_delete])
    # Updates
    operations.extend([UpdateGroupOperation(g, c) for g, c in get_update_list(remaining_pairs)])
    return operations


def sync_members(group: GraphGroup, local: List[GraphUser], remote: List[GraphUser]) -> List[SyncOperation]:
    """Returns the necessary operations to sync the members of given group."""
    operations = []
    # Create+delete
    to_create, to_delete, remaining_pairs = get_create_delete(local, remote)
    operations.extend([AddGroupMemberOperation(group, u) for u in to_create])
    operations.extend([RemoveGroupMemberOperation(group, u) for u in to_delete])
    return operations


def get_create_delete(change_to: List[GraphObject], to_change: List[GraphObject]) -> Tuple[List, List, List[Tuple]]:
    """Returns the needed changes to turn one list into the other.

    Only returns creations and deletions, not updates.

    Returns:
        A 3-tuple with (to_create, to_delete, remaining_pairs). Each list contains
            GraphObject instances. The remaining_pairs is a list
            of 2-tuples with the change_to object and to_change object.
    """
    # Create mappings on Tutti database ID
    change_to_map = {o.extension["tuttiId"]: o for o in change_to}
    to_change_map = {o.extension["tuttiId"]: o for o in to_change}

    create_ids = change_to_map.keys() - to_change_map.keys()
    delete_ids = to_change_map.keys() - change_to_map.keys()
    ids_in_both = change_to_map.keys() - create_ids
    return ([change_to_map[i] for i in create_ids],
            [to_change_map[i] for i in delete_ids],
            [(change_to_map[i], to_change_map[i]) for i in ids_in_both])


def get_update_list(object_pairs: List[Tuple[GraphObject, GraphObject]]) -> List[Tuple]:
    """Compares all object pairs and returns the ones with updates.

    Returns:
        A list of (object, changes) pairs, where the object is the original
            unchanged object from the pair, and changes is a dictionary of
            field changes that need to be applied to that object.
    """
    updates = []
    for change_to, to_change in object_pairs:
        update_dict = get_update(change_to, to_change)
        if update_dict:
            updates.append((to_change, update_dict))
    return updates


def get_update(change_to: GraphObject, to_change: GraphObject) -> Dict:
    """Returns the fields that differ between the two Graph directory objects.

    Removed fields get a None value.
    """
    change_to = change_to.as_object()
    to_change = to_change.as_object()
    # Deletions
    deletions = to_change.keys() - change_to.keys()
    differs = {k: None for k in deletions}
    # Additions+changes
    for key, new_value in change_to.items():
        original_value = to_change.get(key, None)
        if new_value != original_value:
            differs[key] = new_value
    return differs
