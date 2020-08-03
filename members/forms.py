from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from ldap3.core.exceptions import LDAPInvalidCredentialsResult

from sync.ldap import get_connection


def try_ldap_bind(user, password):
    """Tries to bind (login) on LDAP with given credentials."""
    conn = get_connection()
    conn.user = user
    conn.password = password
    try:
        conn.bind()
    except LDAPInvalidCredentialsResult:
        return False
    finally:
        conn.unbind()
    return True


class MyPasswordChangeForm(PasswordChangeForm):
    """Password change form that verifies old passwords on LDAP."""

    def clean_old_password(self):
        # Passwords that are only set in LDAP have value 'invalid' in Django
        if self.user.password == "invalid":
            # Try LDAP bind
            old_password = self.cleaned_data["old_password"]
            ldap_user = "uid={},ou=people,dc=esmgquadrivium,dc=nl".format(self.user.username)
            if not try_ldap_bind(ldap_user, old_password):
                raise forms.ValidationError(
                    self.error_messages['password_incorrect'],
                    code='password_incorrect',
                )
            # Bind succeeded
            return old_password
        return super().clean_old_password()
