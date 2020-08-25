from django.contrib import admin
from activities.models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Admin page for activities."""
    fieldsets = [
        (None, {'fields': ('name', 'description', 'location', 'cost', 'owners')}),
        ("Dates", {'fields': ('start_date', 'end_date', 'closing_date')}),
        ("Settings", {'fields': ('hide_activity', 'hide_participants', 'groups')}),
    ]
    autocomplete_fields = ('groups', 'owners')
