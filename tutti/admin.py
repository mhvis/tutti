from django.contrib import admin


class TuttiAdminSite(admin.AdminSite):
    """Admin site branding."""

    site_header = "Members admin"
    site_title = "Tutti"
    index_title = "Members admin"

    def has_permission(self, request):
        # Allow everyone to access the admin site (normally the user needs to be staff)
        #  Users will need to have explicit permissions assigned in order to be able to do something
        return request.user.is_active
