from datetime import date, datetime, timezone

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from faqts.graphing import pie, date_plot, group_membership_counts
from members.models import QGroup, Person, Instrument
from django.db.models import Count

from django.views.generic import TemplateView


class FaQtsView(LoginRequiredMixin, TemplateView):
    template_name = "faqts/faqts.html"

    def get_context_data(self, **kwargs):
        groups = QGroup.objects.all()
        persons = Person.objects.all()
        double_names = list(Person.objects.values('first_name').annotate(
            name_count=Count('first_name')).filter(
            name_count__gt=1).values_list('first_name', flat=True))
        double_name_counts = list(Person.objects.values('first_name').annotate(
            name_count=Count('first_name')).filter(
            name_count__gt=1).values_list('first_name', 'name_count'))
        persongroupvalues = list(Person.objects.all().values('first_name', 'last_name', 'groups').values_list(
            'first_name', 'last_name', 'groups'))
        instruments = Instrument.objects.all()

        member_qs = Person.objects.filter_members()

        student_counts = (member_qs.filter(is_student=True).count(),
                          member_qs.filter(is_student=False).count())


        dates, count = group_membership_counts(QGroup.objects.get_members_group())
        idx = dates > datetime(2018, 1, 1, tzinfo=timezone.utc)
        members_plot = date_plot(dates[idx], count[idx])

        dates, count = group_membership_counts(QGroup.objects.get(name="Ensuite"))
        idx = dates > datetime(2020, 4, 2, tzinfo=timezone.utc)
        ensuite_plot = date_plot(dates[idx], count[idx])

        dates, count = group_membership_counts(QGroup.objects.get(name="Bestuur"))
        idx = dates > datetime(2020, 4, 2, tzinfo=timezone.utc)
        board_plot = date_plot(dates[idx], count[idx])

        dates, count = group_membership_counts(QGroup.objects.get(name="Vokollage"))
        idx = dates > datetime(2020, 4, 2, tzinfo=timezone.utc)
        vokollage_plot = date_plot(dates[idx], count[idx])

        dates, count = group_membership_counts(QGroup.objects.get(name="Auletes"))
        idx = dates > datetime(2020, 4, 2, tzinfo=timezone.utc)
        auletes_plot = date_plot(dates[idx], count[idx])


        context = {
            'groups': groups,
            'persons': persons,
            'double_names': double_names,
            'double_name_counts': double_name_counts,
            'instruments': instruments,
            'persongroupvalues': persongroupvalues,
            'student_plot': pie(student_counts, ('Student', 'Not a student')),
            'test_plot': date_plot([date(2020, 1, 1), date(2020, 2, 1), date(2020, 3, 15)], [5, 4, 3]),
            'members_count_plot': members_plot,
            'ensuite_plot': ensuite_plot,
            'vokollage_plot': vokollage_plot,
            'auletes_plot': auletes_plot,
            'board_plot': board_plot,
        }
        return context
