"""Module for one-way sync between two datasets."""
from typing import List, Dict

from ldapsync.ldap import LDAP_ATTRIBUTE_TYPES
from ldapsync.ldapoperations import LDAPOperation


def sync(source: Dict[str, Dict[str, List[LDAP_ATTRIBUTE_TYPES]]],
         target: Dict[str, Dict[str, List[LDAP_ATTRIBUTE_TYPES]]],
         on="qDBLinkID") -> List[LDAPOperation]:
    """Get operations to perform to change the target dataset to be the same as the source dataset.

    The source and target are dictionaries of LDAP entries. The dictionary key is the Distinguished Name of an entry,
    the value is a dictionary of entry attributes to list of values.

    Args:
        source: Source dataset.
        target: Target dataset, the dataset that needs to be modified.
        on: Attribute that will be used to match source entries with target entries.

    Returns:
        A list of add, delete, modify operations.
    """
    pass


"""
def get_add_delete(ldap_entries, model: SyncModel) -> List[SyncOperation]:
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
"""
