"""Module for communication with the LDAP database."""
from collections import namedtuple
from datetime import datetime
from typing import List, Dict, Union

from django.conf import settings
from ldap3 import Server, Connection

LDAP_ATTRIBUTE_TYPES = Union[str, int, datetime, bool]
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


def get_ldap_entries(conn: Connection,
                     *search: LDAPSearch) -> Dict[str, Dict[str, List[LDAP_ATTRIBUTE_TYPES]]]:
    """Get data from the LDAP database.

    Args:
        conn: LDAP connection.
        search: What to get from the database.

    Returns:
        A dictionary with all retrieved entries from LDAP. The format of the
        dictionary is {DN -> {attribute -> [values]}}.
    """
    pass


"""
        # Get entries on the LDAP server that have a link with a Django model
        search_filter = '(&(objectClass={})({}=*))'.format(model.object_class,
                                                           model.link_attribute)
        conn.search(search_base=model.base_dn,
                    search_filter=search_filter,
                    search_scope=LEVEL,
                    attributes=list(model.attribute_keys) + [model.link_attribute])
"""
