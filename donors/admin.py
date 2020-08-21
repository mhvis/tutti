from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportMixin

from donors.models import Donor


class DonorAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("first_name", "last_name", "email", "salutation")}),
        ("Address", {"fields": ("street", "postal_code", "city", "country")}),
        ("Donation info", {"fields": ("iban", "amount", "newsletter")}),
    )


# Import/export

class DonorResource(resources.ModelResource):
    class Meta:
        model = Donor
        # It's possible to bulk update records by exporting and reimporting,
        # the applied changes are previewed.
        skip_unchanged = True
        report_skipped = False


@admin.register(Donor)
class DonorImportExportAdmin(ImportExportMixin, DonorAdmin):
    """DonorAdmin extended with import/export capabilities."""
    resource_class = DonorResource

    def has_import_permission(self, request):
        return self.has_change_permission(request)

    def has_export_permission(self, request):
        return self.has_view_permission(request)
