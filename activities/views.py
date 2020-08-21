from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from activities.models import Activity


class ActivityView(LoginRequiredMixin, TemplateView):
    """Displays an activity."""
    template_name = "activities/activity.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "activities": Activity.objects.all(),
        })
        return context
