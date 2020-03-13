"""Module for communication with the LDAP database."""
from collections import namedtuple
from datetime import datetime
from typing import List, Dict, Union, Iterable

from django.conf import settings
from ldap3 import Server, Connection, LEVEL

LDAPAttributeType = Union[str, int, datetime, bool]
"""Possible types for LDAP attribute values."""


def get_connection():
    """Opens a new LDAP connection, use as context manager."""
    server = Server(settings.LDAP['HOST'])
    conn = Connection(server=server,
                      user=settings.LDAP['USER'],
                      password=settings.LDAP['PASSWORD'],
                      raise_exceptions=True)
    if settings.LDAP['START_TLS']:
        conn.start_tls(read_server_info=False)
    return conn


LDAPSearch = namedtuple('LDAPSearch', ['base_dn', 'object_class', 'attributes'])
"""Specifies parameters for an LDAP search: base DN, object class and attributes."""


def _normalize_attrs(attrs: Dict) -> Dict:
    """Make sure that every value is a list, also for single-valued attributes."""
    return {k: v if isinstance(v, list) else [v] for k, v in attrs.items()}


def get_ldap_entries(conn: Connection,
                     search: Iterable[LDAPSearch]) -> Dict[str, Dict[str, List[LDAPAttributeType]]]:
    """Get data from the LDAP database.

    Args:
        conn: LDAP connection.
        search: What to get from the database.

    Returns:
        A dictionary with all retrieved entries from LDAP. The format of the
        dictionary is {DN -> {attribute -> [values]}}.
    """
    entries = {}
    for s in search:
        search_filter = '(objectClass={})'.format(s.object_class)
        conn.search(search_base=s.base_dn,
                    search_filter=search_filter,
                    search_scope=LEVEL,
                    attributes=s.attributes)
        for response_entry in conn.response:
            entries[response_entry['dn']] = _normalize_attrs(response_entry['attributes'])

    return entries
