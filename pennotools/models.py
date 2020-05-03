from django.db import models


class Permissions(models.Model):
    """Model that defines the app permissions, does not create a database."""

    class Meta:
        managed = False  # No db
        permissions = (
            ('can_access', 'Can use the treasurer tools'),  # Can do everything in this app
        )
        default_permissions = ()  # No default permissions (add/delete/view/change)
