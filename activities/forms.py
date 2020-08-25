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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = "Name of the activity"
        self.fields['start_date'].help_text = "Start time and date of the activity"
        self.fields['end_date'].help_text = "End time and date of the activity"
        self.fields['closing_date'].help_text = "Time and date enlisting closes"
