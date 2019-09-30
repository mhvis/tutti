from django.apps import AppConfig


class LdapProxyConfig(AppConfig):
    name = 'ldapproxy'

    def ready(self):
        import ldapproxy.signals
