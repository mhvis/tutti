from django import forms

from activities.models import Activity


class ActivityForm(forms.ModelForm):
    """Allows the user to change an activity."""

    class Meta:
        model = Activity
        fields = ['name',
                  'description',
                  'cost',
                  'location',
                  'start_date',
                  'end_date',
                  'closing_date',
                  'hide_activity',
                  'hide_participants',
                  'groups',
                  ]
