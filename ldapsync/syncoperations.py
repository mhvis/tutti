from ldap3 import Connection

from ldapsync.models import SyncModel


class SyncOperation:
    """Base class for LDAP sync operations (add/delete/modify)."""

    def apply(self, conn: Connection):
        """Perform the operation on an LDAP connection."""
        raise NotImplementedError()


class AddOperation(SyncOperation):
    """Adds the specified Django instance on LDAP."""

    def __init__(self, instance: SyncModel):
        self.instance = instance

    def __str__(self) -> str:
        return 'Add instance: {}'.format(self.instance)


class DeleteOperation(SyncOperation):
    """Removes an LDAP entry."""

    def __init__(self, model: SyncModel, link_id: int):
        """Constructor.

        Args:
            model: The model type.
            link_id: The LDAP link ID value of the entry to delete.
        """
        self.model = model
        self.link_id = link_id

    def __str__(self) -> str:
        return 'Delete ID {} of model {}'.format(self.link_id, self.model)


class ModifyOperation(SyncOperation):
    """Updates a single attribute of a model by overwriting it."""

    def __init__(self, instance: SyncModel, attribute_key: str):
        self.instance = instance
        self.attribute_key = attribute_key

    def __str__(self) -> str:
        return 'Modify attribute {} on instance {}'.format(self.attribute_key,
                                                           self.instance)


class ModifyDNOperation(SyncOperation):
    """Modifies the DN of an LDAP entry."""

    def __init__(self, instance: SyncModel):
        self.instance = instance

    def __str__(self) -> str:
        return 'Modify DN on instance {}'.format(self.instance)
