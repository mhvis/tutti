"""Module for communication with the LDAP database."""
from collections import namedtuple
from datetime import datetime
from typing import List, Dict, Union, Iterable

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from ldap3 import Server, Connection, LEVEL

LDAPAttributeType = Union[str, int, datetime, bool]
"""Possible types for LDAP attribute values."""


def get_connection():
    """Opens a new LDAP connection, use as context manager."""
    # Need to have a host setup
    if not settings.LDAP_HOST:
        raise ImproperlyConfigured("LDAP host not setup.")
    server = Server(settings.LDAP_HOST)
    conn = Connection(server=server,
                      user=settings.LDAP_USER,
                      password=settings.LDAP_PASSWORD,
                      raise_exceptions=True)
    if settings.LDAP_START_TLS:
        conn.start_tls(read_server_info=False)
    return conn


LDAPSearch = namedtuple('LDAPSearch', ['base_dn', 'object_class', 'attributes'])
"""Specifies parameters for an LDAP search: base DN, object class and attributes."""


def _normalize_attrs(attrs: Dict) -> Dict:
    """Make sure that every value is a list, also for single-valued attributes.

    Discards empty lists.
    """
    # Convert to list
    result = {k: v if isinstance(v, list) else [v] for k, v in attrs.items()}
    # Discard empty lists
    result = {k: v for k, v in result.items() if v}
    return result


def _normalize_dn(dn: str) -> str:
    """Make DN lowercase."""
    return dn.lower()


def get_ldap_entries(conn: Connection,
                     search: Iterable[LDAPSearch]) -> Dict[str, Dict[str, List[LDAPAttributeType]]]:
    """Get data from the LDAP database.

    Args:
        conn: LDAP connection.
        search: What to get from the database.

    Returns:
        A dictionary with all retrieved entries from LDAP. The format of the
            dictionary is {DN -> {attribute -> [values]}}. The entries are
            normalized, i.e. DNs are all lowercase.
    """
    entries = {}
    for s in search:
        search_filter = '(objectClass={})'.format(s.object_class)
        conn.search(search_base=s.base_dn,
                    search_filter=search_filter,
                    search_scope=LEVEL,
                    attributes=s.attributes)
        for response_entry in conn.response:
            dn = _normalize_dn(response_entry['dn'])
            attrs = _normalize_attrs(response_entry['attributes'])
            entries[dn] = attrs

    return entries
