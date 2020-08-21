from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from activities.models import Activity


class ActivitiesView(LoginRequiredMixin, TemplateView):
    """Displays a list of activities."""
    template_name = "activities/activities.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "activities": Activity.objects.all(),
        })
        return context

class ActivityView(LoginRequiredMixin, TemplateView):
    """Displays an activity."""
    template_name = "activities/activity.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activity = Activity.objects.get(id=context['id'])
        participants = activity.participants.all()
        for participant in participants:
            print(participant)
        context.update({
            "activity": activity,
            "participants": participants,
        })
        return context

    def get_queryset(self):
        activity = get_object_or_404(Activity, id=self.kwargs['id'])
        return activity
