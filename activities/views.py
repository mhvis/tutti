from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from activities.models import Activity
from members.models import User, Person


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

    def get(self, request, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        activity = Activity.objects.get(id=context['id'])
        participants = activity.participants.all()
        persons = activity.participants.filter(username=request.user.username)
        for participant in participants:
            print(participant)
        context.update({
            "activity": activity,
            "participants": participants,
            "is_subscribed": (persons.count() > 0),
        })
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        try:
            user = User.objects.get(username=request.user.username)
        except ObjectDoesNotExist:
            return self.get(request, form_invalid=True, id=context['id'])

        try:
            person = Person.objects.get(username=user.username)
        except ObjectDoesNotExist:
            return self.get(request, person_invalid=True, id=context['id'])

        """Add or remove person from the activity"""
        activity = Activity.objects.get(id=context['id'])
        if 'signup' in request.POST:
            activity.participants.add(person)
        else:
            activity.participants.remove(person)

        return self.get(request, id=context['id'])

    def get_queryset(self):
        activity = get_object_or_404(Activity, id=self.kwargs['id'])
        return activity