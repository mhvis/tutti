"""LDAP add, delete and modify operations."""
from typing import Dict, List, Optional, Tuple

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
        # Note! The LDAP server complains if an attribute has an empty list as the value.
        conn.add(self.dn, attributes=self.attributes)


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
        # if not self.values or not self.values[0]:
        #     self.values = None
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
        dn, relative_dn, new_superior = self._get_modify_dn_args()
        conn.modify_dn(dn, relative_dn, new_superior=new_superior)

    def _get_modify_dn_args(self) -> Tuple[str, str, Optional[str]]:
        """Returns DNs in the correct format for the modify_dn function.

        See https://ldap3.readthedocs.io/en/latest/modifydn.html.

        Returns:
            A 3 tuple with (old DN | first component of new DN | rest of new DN
            if different else None).
        """
        old_dn_parts = self.dn.partition(",")
        new_dn_parts = self.new_dn.partition(",")
        new_superior = None
        if old_dn_parts[2].lower() != new_dn_parts[2].lower():
            new_superior = new_dn_parts[2]
        return self.dn, new_dn_parts[0], new_superior
