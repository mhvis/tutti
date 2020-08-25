from django.contrib import admin
from activities.models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Admin page for activities."""
    fields = ('name',
              'description',
              'hide_activity',
              'hide_participants',
              'cost',
              'location',
              'start_date',
              'end_date',
              'closing_date',
              'groups',
              'participants',
              'owners')
    filter_horizontal = ('groups', 'participants', 'owners')
