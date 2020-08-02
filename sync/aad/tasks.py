"""Tasks for running synchronization."""
from typing import List

from sync.aad.graph import Graph
from sync.aad.operations import SyncOperation, DeleteUserOperation, DeleteGroupOperation
from sync.aad.sync import aad_sync_objects, aad_sync_members


def apply(operations: List[SyncOperation], graph: Graph) -> List[SyncOperation]:
    for o in operations:
        o.apply(graph)
    return operations


def aad_sync(apply_deletions=False) -> List[SyncOperation]:
    """Runs full sync with Azure Active Directory.

    Args:
        apply_deletions: If True, delete operations will be applied as well.
            Disabled by default to prevent accidental deletion of objects in
            case of a bug. Leftover users or groups in AAD usually don't pose a
            problem, a manual sync can be run sometimes to clean the deleted
            objects.

    Returns:
        The operations that have been applied.
    """
    graph = Graph.from_settings()
    applied = []
    # Sync groups and users
    object_operations = aad_sync_objects(graph)
    # Split out delete operations
    delete_ops = []
    non_delete_ops = []
    for o in object_operations:
        if isinstance(o, DeleteUserOperation) or isinstance(o, DeleteGroupOperation):
            delete_ops.append(o)
        else:
            non_delete_ops.append(o)
    applied.extend(apply(non_delete_ops, graph))
    if apply_deletions:
        applied.extend(apply(delete_ops, graph))
    # Sync group memberships
    membership_operations = aad_sync_members(graph)
    applied.extend(apply(membership_operations, graph))
    return applied
