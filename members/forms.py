from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from ldap3.core.exceptions import LDAPInvalidCredentialsResult

from members.models import Person, MembershipRequest
from sync.ldap import get_connection


class ProfileForm(forms.ModelForm):
    """Allows the user to change some of his profile data."""

    class Meta:
        model = Person
        fields = ["email", "phone_number", "street", "postal_code", "city", "country",
                  "preferred_language"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            "email"].help_text = "If you change your email address, members mail will be sent to the new address."


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


class SubscribeForm(forms.ModelForm):
    class Meta:
        model = MembershipRequest
        fields = ['first_name', 'last_name', 'initials', 'email', 'phone_number', 'street', 'postal_code', 'city',
                  'country', 'gender', 'date_of_birth', 'preferred_language', 'field_of_study', 'is_student', 'iban',
                  'tue_card_number', 'remarks', 'sub_association', 'instruments']
        help_texts = {
            'initials': "Voorletters.",
            'tue_card_number': "If you have a TU/e campus card, fill in the number that is printed sideways "
                               "(not your student number or s-number). We will then make it possible for you to enter "
                               "the cultural section in Luna, using your campus card, during off-hours. During the "
                               "day however the entrance is usually always open to anyone.",
        }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     for key, field in self.fields.items():
    #         field.required = True
