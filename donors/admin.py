from django.contrib import admin

from donors.models import Donor


class DonorAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("first_name", "last_name", "email", "salutation")}),
        ("Address", {"fields": ("street", "postal_code", "city", "country")}),
        ("Donation info", {"fields": ("iban", "amount", "newsletter")}),
    )


admin.site.register(Donor, DonorAdmin)
