from datetime import datetime

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.views.generic import TemplateView, View

from members.models import Person


class DuqduqgoAccessMixin(PermissionRequiredMixin):
    """Use this mixin to protect views from prying eyes."""
    permission_required = 'duqduqgo.can_access'


class Qalendar(DuqduqgoAccessMixin, TemplateView):
    template_name = "duqduqgo/qalendar.html"


class Birthdays(DuqduqgoAccessMixin, View):

    def get(self, request, *args, **kwargs):
        r_date_start = datetime.strptime(request.GET.get('start', '')[0:10], '%Y-%m-%d')
        # r_date_end = datetime.strptime(request.GET.get('end', '')[0:10], '%Y-%m-%d')
        print(r_date_start)
        persons = Person.objects.filter(date_of_birth__isnull=False)
        # persons = Person.objects.filter(date_of_birth__month__gte=r_date_start.month,
        #                                date_of_birth__month__lte=r_date_end.month)
        print(persons)
        calendar_events = []
        for person in persons:
            date_1 = datetime(r_date_start.year, person.date_of_birth.month, person.date_of_birth.day).date()
            date_2 = datetime(r_date_start.year + 1, person.date_of_birth.month, person.date_of_birth.day).date()
            calendar_events.append({
                "title": person.get_full_name(),
                "start": str(date_1),
                "end": str(date_1)
            })
            calendar_events.append({
                "title": person.get_full_name(),
                "start": str(date_2),
                "end": str(date_2)
            })
        return JsonResponse(calendar_events, safe=False)
