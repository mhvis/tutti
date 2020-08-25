from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy

from activities.models import Activity
from activities.forms import ActivityForm
from members.models import User, Person, GroupMembership


def can_view_activity(person: Person, activity: Activity) -> bool:
    for membership in GroupMembership.objects.filter(user=person, end=None):
        for activity_group in activity.groups.all():
            if (activity_group.id == membership.group.id
                    and not activity.hide_activity
                    or person.is_staff
                    or person in activity.owners.all()):
                return True
    return False


def can_edit_activity(person: Person, activity: Activity) -> bool:
    return person in activity.owners.all() or person.is_staff


class MyActivityFormView(LoginRequiredMixin, FormView):
    """Displays a form to edit an activity."""
    template_name = "activities/my_activity.html"
    form_class = ActivityForm
    success_url = reverse_lazy("activities:index")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        activity = Activity.objects.get(id=self.kwargs['id'])
        kwargs["instance"] = activity
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(MyActivityFormView, self).get_context_data(**kwargs)
        activity = Activity.objects.get(id=self.kwargs['id'])
        context["can_edit"] = can_edit_activity(self.request.user.person, activity)
        context["activity"] = activity
        context["participants"] = activity.participants.all()
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class ActivitiesView(LoginRequiredMixin, TemplateView):
    """Displays a list of activities."""
    template_name = "activities/activities.html"

    def get(self, request, *args, **kwargs):
        person = Person.objects.get(username=request.user.username)
        context = super().get_context_data(**kwargs)
        activities = []
        can_edit = []
        for activity in Activity.objects.all():
            if can_view_activity(person, activity) and activity not in activities:
                activities.append(activity)
            if can_edit_activity(person, activity) and activity.id not in can_edit:
                can_edit.append(activity.id)

        context.update({
            "activities": activities,
            "title": "Activities",
            "can_edit": can_edit,
        })
        return self.render_to_response(context)


class ActivityView(LoginRequiredMixin, TemplateView):
    """Displays an activity."""
    template_name = "activities/activity.html"

    def get(self, request, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        activity = Activity.objects.get(id=context['id'])
        person = Person.objects.get(username=request.user.username)
        participants = activity.participants.all()
        persons = activity.participants.filter(username=request.user.username)
        context.update({
            "activity": activity,
            "participants": None if activity.hide_participants else participants,
            "is_subscribed": (persons.count() > 0),
            "can_edit": can_edit_activity(person, activity),
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
        if not can_view_activity(person, activity):
            return self.get(request, no_permission=True, id=context['id'])

        if activity.is_closed:
            return self.get(request, form_invalid=True, id=context['id'])

        if 'signup' in request.POST:
            activity.participants.add(person)
        else:
            activity.participants.remove(person)

        return self.get(request, id=context['id'])

    def get_queryset(self):
        activity = get_object_or_404(Activity, id=self.kwargs['id'])
        return activity
