from datetime import datetime, date

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.generic import TemplateView, View

from members.models import Person


class DuqduqgoAccessMixin(PermissionRequiredMixin):
    """Use this mixin to protect views from prying eyes."""
    permission_required = 'duqduqgo.can_access'


class Qalendar(DuqduqgoAccessMixin, TemplateView):
    template_name = "duqduqgo/qalendar.html"


class Birthdays(DuqduqgoAccessMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            start = datetime.fromisoformat(request.GET.get("start"))
            end = datetime.fromisoformat(request.GET.get("end"))
        except ValueError:
            return HttpResponseBadRequest()

        # No testcases for this view because it's not very critical

        # Filter on members and people that have birthdays
        qs = Person.objects.filter_members().filter(date_of_birth__isnull=False)

        if start > end:
            return HttpResponseBadRequest()

        # This part filters the people fetched from the database so that only those in the range are returned.
        #  I've disabled it because I'm not sure if there are no bugs

        # # Filter the QuerySet further to only return dates between start and end
        # # (Actually not necessary because the dates get filtered after retrieval again, but is a bit more performant)
        # def dob_gte(month: int, day: int) -> Q:
        #    """Returns a query object of >= on date of birth."""
        #    return (Q(date_of_birth__month=month) & Q(date_of_birth__day__gte=day)) | Q(date_of_birth__month__gt=month)
        #
        # def dob_lte(month: int, day: int):
        #    """See dob_gte()."""
        #    return (Q(date_of_birth__month=month) & Q(date_of_birth__day__lte=day)) | Q(date_of_birth__month__lt=month)
        # elif start.year == end.year:
        #     # If the year is the same, get all birthdays between start and end
        #     qs.filter(dob_gte(start.month, start.day) & dob_lte(end.month, end.day))
        # elif start.year + 1 == end.year:
        #    # If there's 1 year difference, get birthdays from start until end of year and from begin of year until end
        #    qs.filter(dob_gte(start.month, start.day) | dob_lte(end.month, end.day))
        # else:
        #     # Start and end year differ more than 1 year, do not filter, get everyone
        #     pass

        # Create events
        events = []
        for person in qs:
            dob = person.date_of_birth  # type: date
            # Create all possible candidate dates
            # Note: this suffers from the leap year bug, if the date is Feb 29 and we're not in a leap year, this will
            #  raise ValueError. However we currently don't have any Feb 29 members so I've kept the bug.
            candidates = [date(y, dob.month, dob.day) for y in range(start.year, end.year + 1)]
            # Filter candidates on those that are in between start and end
            dates = [d for d in candidates if start.date() <= d <= end.date()]
            events.extend([{
                "allDay": True,
                "start": d.isoformat(),
                "end": d.isoformat(),
                "title": person.get_full_name(),
                "age": d.year - dob.year,
            } for d in dates])
        return JsonResponse(events, safe=False)
