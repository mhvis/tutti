"""Configuration for login using OpenID Connect.

The account is retrieved via the username, if the account does not exist, the
user can't login.
"""
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class MyOIDCAB(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        username = claims.get('username')
        if not username:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(username__iexact=username)

# Todo: when a user logs out of this site it should also log out at the identity provider (Keycloak)
# def provider_logout(request):
#     # See your provider's documentation for details on if and how this is
#     # supported
#     redirect_url = 'https://myprovider.com/logout'
#     return redirect_url
