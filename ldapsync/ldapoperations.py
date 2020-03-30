"""LDAP add, delete and modify operations."""
from typing import Dict, List

from ldap3 import Connection, MODIFY_REPLACE


class LDAPOperation:
    """Base class for LDAP sync operations (add/delete/modify)."""

    def apply(self, conn: Connection):
        """Perform the operation on an LDAP connection."""
        raise NotImplementedError()


class AddOperation(LDAPOperation):
    """Add a new entry."""

    def __init__(self, dn: str, attributes: Dict[str, List[str]]):
        """Add a new entry.

        Args:
            dn: Distinguished Name.
            attributes: A dictionary from attributes to list of values.
        """
        self.dn = dn
        self.attributes = attributes

    def __str__(self) -> str:
        return 'Add {} with {}'.format(self.dn, self.attributes)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, AddOperation):
            return self.dn == o.dn and self.attributes == o.attributes
        return False

    def apply(self, conn: Connection):
        conn.add(self.dn, self.attributes['objectClass'], self.attributes)


class DeleteOperation(LDAPOperation):
    """Delete an LDAP entry."""

    def __init__(self, dn: str):
        """Delete.

        Args:
            dn: Distinguished Name of the entry.
        """
        self.dn = dn

    def __str__(self) -> str:
        return 'Delete {}'.format(self.dn)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, DeleteOperation):
            return self.dn == o.dn
        return False

    def apply(self, conn: Connection):
        conn.delete(self.dn)


class ModifyOperation(LDAPOperation):
    """Modify a single attribute.

    If the attribute does not exist it will be created. If the list of (new)
    values is empty, the attribute will be removed.
    """

    def __init__(self, dn: str, attribute: str, values: List[str]):
        """Modify a single attribute.

        Args:
            dn: Distinguished Name.
            attribute: Attribute name.
            values: New values for the attribute. If empty, the attribute will
                be removed.
        """
        self.dn = dn
        self.attribute = attribute
        self.values = values

    def __str__(self) -> str:
        return 'Modify {}: set {} to {}'.format(self.dn, self.attribute, self.values)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, ModifyOperation):
            # Order of values doesn't matter
            values_equal = sorted(self.values) == sorted(o.values)
            return self.dn == o.dn and self.attribute == o.attribute and values_equal
        return False

    def apply(self, conn: Connection):
        conn.modify(self.dn, {self.attribute: [(MODIFY_REPLACE, self.values)]})


class ModifyDNOperation(LDAPOperation):
    """Modify the DN of an LDAP entry."""

    def __init__(self, dn: str, new_dn: str):
        self.dn = dn
        self.new_dn = new_dn

    def __str__(self) -> str:
        return 'Modify DN of {} to {}'.format(self.dn, self.new_dn)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, ModifyDNOperation):
            return self.dn == o.dn and self.new_dn == o.new_dn
        return False

    def apply(self, conn: Connection):
        conn.modify_dn(self.dn, self.new_dn)
