from django.contrib import admin
from activities.models import Activity
from members.admin import admin_site


@admin.register(Activity, site=admin_site)
class ActivityAdmin(admin.ModelAdmin):
    """Admin page for activities."""
    fields = ('name', 'description', 'date', 'closing_date', 'groups', 'participants')
    list_filter = ('groups', 'participants')
