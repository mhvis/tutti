"""High level LDAP sync functions."""
from typing import List

from ldap3 import Connection

from sync.ldap import get_ldap_entries, get_connection
from sync.ldapentities import LDAPPerson, LDAPGroup
from sync.ldapoperations import LDAPOperation
from sync.sync import sync


def get_ldap_sync_operations(conn: Connection) -> List[LDAPOperation]:
    """Compares local and remote data and returns sync operations."""
    # Retrieve local and remote entries
    local_people = LDAPPerson.get_entries()
    local_groups = LDAPGroup.get_entries()
    remote_people = get_ldap_entries(conn, [LDAPPerson.get_search()])
    remote_groups = get_ldap_entries(conn, [LDAPGroup.get_search()])
    # The people and groups need to be synced separately because they
    #  are matched on their primary key, which is only unique within
    #  people and groups, but not unique if you take those together.
    operations = sync(local_people, remote_people)
    operations += sync(local_groups, remote_groups)
    return operations


def ldap_sync() -> List[LDAPOperation]:
    """Do a full LDAP sync.

    Returns:
        The sync operations that have been applied.
    """
    with get_connection() as conn:
        operations = get_ldap_sync_operations(conn)
        for operation in operations:
            operation.apply(conn)
    return operations
