"""Import export resources."""

from import_export import resources

from members.models import Person


class PersonResource(resources.ModelResource):
    class Meta:
        model = Person
        # It's possible to bulk update records by exporting and reimporting,
        # the applied changes are previewed.
        skip_unchanged = True
        report_skipped = False
        # Mostly exclude built-in Django User fields
        exclude = ('user_ptr', 'password', 'is_superuser', 'user_permissions', 'is_staff', 'is_active', 'last_login',
                   'date_joined', 'ldap_password')
