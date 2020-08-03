from django.contrib.admin.apps import AdminConfig


class TuttiAdminConfig(AdminConfig):
    """Admin site branding."""
    default_site = "tutti.admin.TuttiAdminSite"
