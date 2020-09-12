from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, FormView, ListView

from activities.forms import ActivityForm
from activities.models import Activity
from members.models import Person, GroupMembership


def can_view_activity(person: Person, activity: Activity) -> bool:
    if person in activity.owners.all() or person.has_perm('activities.view_activity'):
        return True
    for membership in GroupMembership.objects.filter(user=person, end=None):
        for activity_group in activity.groups.all():
            if activity_group.id == membership.group.id and not activity.hide_activity:
                return True
    return False


def can_edit_activity(person: Person, activity: Activity) -> bool:
    # We can use the below permission to grant board members edit access for all activities
    return person in activity.owners.all() or person.has_perm('activities.change_activity')


class MyActivityFormView(LoginRequiredMixin, FormView):
    """Displays a form to edit an activity."""
    template_name = "activities/my_activity.html"
    form_class = ActivityForm
    success_url = reverse_lazy("activities:index")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Check access
        activity = Activity.objects.get(id=self.kwargs['id'])
        if not can_edit_activity(self.request.user.person, activity):
            raise PermissionDenied
        kwargs["instance"] = Activity.objects.get(id=self.kwargs['id'])
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class ActivitiesView(LoginRequiredMixin, ListView):
    """Displays a list of activities."""
    template_name = "activities/activities.html"

    def get_queryset(self):
        return Activity.objects.filter(start_date__gte=timezone.now()).order_by('start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.request.user.person
        activities = []
        can_edit = []
        for activity in self.get_queryset():
            if can_view_activity(person, activity) and activity not in activities:
                activities.append(activity)
            if can_edit_activity(person, activity) and activity.id not in can_edit:
                can_edit.append(activity.id)

        context.update({
            "activities": activities,
            "can_edit": can_edit,
        })
        return context


class PastActivitiesView(ActivitiesView):
    template_name = 'activities/past_activities.html'

    def get_queryset(self):
        return Activity.objects.filter(start_date__lt=timezone.now()).order_by('-start_date')


class ActivityView(LoginRequiredMixin, TemplateView):
    """Displays an activity."""
    template_name = "activities/activity.html"

    def get_activity(self):
        """Returns the activity (if the user has view access)."""
        activity = Activity.objects.get(id=self.kwargs['id'])
        # Check permission
        if not can_view_activity(self.request.user.person, activity):
            raise PermissionDenied
        return activity

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        activity = self.get_activity()
        participants = activity.participants.all()
        persons = activity.participants.filter(username=self.request.user.username)
        context.update({
            "activity": activity,
            "participants": None if activity.hide_participants else participants,
            "is_subscribed": persons.exists(),
            "can_edit": can_edit_activity(self.request.user.person, activity),
        })
        return context

    def post(self, request, *args, **kwargs):
        # This might throw Person.DoesNotExist when accessed by a user without a related Person instance,
        #  but that only happens in development.
        person = request.user.person

        # Add or remove person from the activity
        activity = self.get_activity()
        if activity.is_closed:
            # Can't change enlistment when activity is closed
            raise PermissionDenied

        if 'signup' in request.POST:
            activity.participants.add(person)
        else:
            activity.participants.remove(person)

        return redirect('activities:activity', id=activity.id)
