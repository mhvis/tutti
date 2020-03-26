"""Registry of OAuth providers."""
from authlib.integrations.django_client import OAuth

oauth = OAuth()

oauth.register(
    'keycloak',
    # Client ID and secret are set in Django settings
    server_metadata_url='https://keycloak.esmgquadrivium.nl/auth/realms/esmgquadrivium/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)
