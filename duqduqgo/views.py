from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from members.models import Person

# Create your views here.
class DuqduqgoAccessMixin(PermissionRequiredMixin):
    """Use this mixin to protect views from prying eyes."""
    permission_required = 'duqduqgo.can_access'

class Qalendar(TemplateView):
    template_name = "duqduqgo/qalendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        persons = Person.objects.all()
        calendar_events = []
        for person in persons:
            calendar_events.append({
                "title": person.first_name,
                "start": "2019-09-05T09:00:00",
                "end": "2019-09-05T18:00:00"
            })
        context['week_birthdays'] = Person.objects.all()
        return context

