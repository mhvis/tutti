from django.conf import settings
from ldap3 import Server, Connection


def get_connection():
    """Open new LDAP connection and return.

    Use as context manager.
    """
    server = Server(settings.LDAP['HOST'])
    conn = Connection(server=server,
                      user=settings.LDAP['USER'],
                      password=settings.LDAP['PASSWORD'],
                      raise_exceptions=True)
    if settings.LDAP['START_TLS']:
        conn.start_tls(read_server_info=False)
    return conn


def raise_for_multi_value(*attributes):
    """Raise exception when a given attribute has more than one values."""
    for a in attributes:
        if len(a.values) > 1:
            raise Exception('Attribute {} for entry {} has more than one values.'.format(a, a.entry))
