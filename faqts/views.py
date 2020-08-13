from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
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
        persongroupvalues = list(Person.objects.all().values('first_name', 'last_name', 'groups').values_list(
                                'first_name', 'last_name','groups'))
        instruments = Instrument.objects.all()
 

        context = {'groups':groups,
                   'persons':persons,
                   'double_names': double_names,
                   'instruments':instruments,
                   'persongroupvalues':persongroupvalues}
        return context
