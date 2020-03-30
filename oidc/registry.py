"""Registry of OAuth providers."""
from authlib.integrations.django_client import OAuth

oauth = OAuth()

oauth.register(
    'keycloak',
    # Client ID and secret are set in Django settings
    server_metadata_url='https://keycloak.esmgquadrivium.nl/auth/realms/esmgquadrivium/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# oauth.register(
#     name='activedirectory',
#     server_metadata_url='https://login.microsoftonline.com/e37b402e-3c13-4bbc-8129-2dcdc6758e6d/v2.0/.well-known/openid-configuration',
#     client_kwargs={'scope': 'openid email profile'},
# )
