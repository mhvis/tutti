"""Module for one-way sync from Django to LDAP ('push')."""

from typing import List

from ldap3 import Connection, LEVEL

from ldapsync.models import SyncModel, SYNC_MODELS
from ldapsync.syncoperations import SyncOperation, AddOperation, DeleteOperation, ModifyDNOperation, ModifyOperation


def get_sync_operations(conn: Connection) -> List[SyncOperation]:
    """Get all sync operations that need to be applied.

    Overview of the types of operations:

    * Entries that exist in Django but are not found in LDAP need to be added
        in LDAP.
    * Entry IDs that are found in LDAP for which there is no Django entry with
        that ID need to be removed from LDAP.
    * Entries in LDAP for which an attribute value differs need to be updated.
    * Entries in LDAP for which the DN attribute value differs, need to be
        updated using a Modify DN operation.
    """
    operations = []
    for model in SYNC_MODELS:
        # Get entries on the LDAP server that have a link with a Django model
        search_filter = '(&(objectClass={})({}=*))'.format(model.object_class,
                                                           model.link_attribute)
        conn.search(search_base=model.base_dn,
                    search_filter=search_filter,
                    search_scope=LEVEL,
                    attributes=list(model.attribute_keys) + [model.link_attribute])

        operations += get_add_delete(conn.entries, model)
        operations += get_modify(conn.entries, model)
    return operations


def get_add_delete(ldap_entries, model: SyncModel) -> List[SyncOperation]:
    """Get add/delete operations that need to be performed on given LDAP entries.

    Args:
        ldap_entries: The entries returned by the LDAP search.
        model: The model type to check for differences.
    """
    # Get set of the primary keys that exist in LDAP
    ldap_ids = set([e[model.link_attribute].value for e in ldap_entries])
    # Get set of primary keys in Django
    django_ids = set([e.pk for e in model.objects.all()])

    to_add = django_ids - ldap_ids  # IDs that exist in Django but not in LDAP
    to_delete = ldap_ids - django_ids  # IDs that exist in LDAP but not in Django

    # Convert to operation instances and return
    add_instances = [model.objects.get(pk=i) for i in to_add]
    add_operations = [AddOperation(i) for i in add_instances]
    delete_operations = [DeleteOperation(model, e) for e in to_delete]
    return add_operations + delete_operations


def get_modify(ldap_entries, model: SyncModel) -> List[SyncOperation]:
    """Get modify and mod_dn operations for a list of LDAP entries.

    Args:
        ldap_entries: An iterable of entries retrieved from an LDAP search.
        model: The Django model specification.
    """
    operations = []
    for entry in ldap_entries:
        # Retrieve Django instance
        pk = entry[model.link_attribute].value
        try:
            instance = model.objects.get(pk=pk)
        except model.DoesNotExist:
            continue

        # Check if DN has changed
        if instance.get_dn().lower() != entry.entry_dn.lower():
            operations.append(ModifyDNOperation(instance))

        # Check for differences in attribute values
        for key, values in instance.get_attribute_values().items():
            if key == model.dn_attribute:
                # DN attribute is ignored as it is modified using MOD_DN
                continue
            ldap_values = set(entry[key].values)
            django_values = set(values)
            if ldap_values != django_values:
                operations.append(ModifyOperation(instance, key))
    return operations


def apply_sync(conn: Connection, operations: List[SyncOperation]):
    """Apply add/modify/delete operations on LDAP."""
    for o in operations:
        o.apply(conn)
