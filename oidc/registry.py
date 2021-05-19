"""Registry of OAuth providers."""
from authlib.integrations.django_client import OAuth

oauth = OAuth()

oauth.register(
    'keycloak',
    # Client ID, secret and metadata URL are set in Django settings
    client_kwargs={'scope': 'openid email profile'},
)
