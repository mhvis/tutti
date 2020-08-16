from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views.generic import TemplateView

from faqts.facts import instrument_counts, group_size_curve
from faqts.graphing import pie, date_plot, hist, bar
from members.models import QGroup, Person, GroupMembership


class FaQtsView(LoginRequiredMixin, TemplateView):
    template_name = "faqts/faqts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        groups = QGroup.objects.all()
        members = Person.objects.filter_members()  # Filter members

        # double_names = list(Person.objects.values('first_name').annotate(
        #     name_count=Count('first_name')).filter(
        #     name_count__gt=1).values_list('first_name', flat=True))

        # persongroupvalues = list(Person.objects.all().values('first_name', 'last_name', 'groups').values_list(
        #     'first_name', 'last_name', 'groups'))

        context.update({
            'groups': groups,
            'persons': members,
            # 'double_names': double_names,
            # 'instruments': instruments,
            # 'persongroupvalues': persongroupvalues,
        })

        # Members plot
        dates, count = group_size_curve(QGroup.objects.get_members_group())
        idx = dates > datetime(2018, 1, 1, tzinfo=timezone.utc)
        context['members_count_plot'] = date_plot(dates[idx], count[idx], title="Number of members over time")

        # Sub-association plots
        context.update({
            'ensuite_plot': date_plot(*group_size_curve(QGroup.objects.get(name="Ensuite")),
                                      title="Ensuite members over time",
                                      from_zero=True),
            'piano_plot': date_plot(*group_size_curve(QGroup.objects.get(name="Pianisten")),
                                    title="Piano members over time",
                                    from_zero=True),
            'vokollage_plot': date_plot(*group_size_curve(QGroup.objects.get(name="Vokollage")),
                                        title="Vokollage members over time",
                                        from_zero=True),
            'auletes_plot': date_plot(*group_size_curve(QGroup.objects.get(name="Auletes")),
                                      title="Auletes members over time",
                                      from_zero=True),
        })

        # Instruments pie chart
        instrument_names, instrument_count = zip(*instrument_counts(cutoff=2))  # Unzip the result
        context['instruments_pie'] = pie(instrument_count, instrument_names, title="Instrument distribution")

        # Language pie chart
        context['language_pie'] = pie(
            (members.filter(preferred_language='nl-nl').count(), members.filter(preferred_language='en-us').count()),
            ("Dutch", "English"),
            title="Language distribution")

        # Gender pie chart
        context['gender_pie'] = pie((members.filter(gender='male').count(), members.filter(gender='female').count()),
                                    ("Male", "Female"),
                                    title="Gender distribution")

        # Birth year histogram
        birth_years = members.filter(date_of_birth__isnull=False).values_list('date_of_birth__year', flat=True)
        context['birth_year_histogram'] = hist(birth_years,
                                               bins=range(min(birth_years), max(birth_years)),
                                               title="Birth years")

        # Length of Q membership
        membership_starts = GroupMembership.objects.filter(group=settings.MEMBERS_GROUP,
                                                           end=None).values_list('start__year', flat=True)
        context['membership_start_histogram'] = hist(membership_starts,
                                                     bins=range(min(membership_starts), max(membership_starts)),
                                                     title="Membership start years")

        # Triplegänger
        triple_name_qs = members.values('first_name').annotate(name_count=Count('first_name')).filter(
            name_count__gte=3).values_list('first_name', 'name_count')
        context['triples_plot'] = bar(*zip(*triple_name_qs),
                                      title="Triplegänger")

        return context


class GroupsView(TemplateView):
    template_name = 'faqts/groups.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # def actual_last_name(last_name: str) -> str:
        #     """Gets rid of 'van'/'de'/... by searching the first capital."""
        #     first_capital_idx = 0
        #     for i in range(len(last_name)):
        #         if last_name[i].isupper():
        #             first_capital_idx = i
        #             break
        #     return last_name[first_capital_idx:]
        #
        # def name_abbr(names: List[str]) -> List[str]:
        #     """Computes shortest possible abbreviations for a list of (last) names.
        #
        #     If some names start with the same letter(s), the abbreviation will be
        #     longer, to be able to differentiate between those.
        #     """
        #     # Todo: this doesn't actually work, it just returns the first letter always
        #     return ["{}.".format(n[0]) for n in names]
        #
        #
        # # Compute double names
        #
        # # Django ORM turned out to be a bit annoying (https://stackoverflow.com/q/8989221) so I changed it by fetching
        # #  all data and doing it in-memory
        #
        # members = Person.objects.filter_members()
        #
        # # Construct dictionary with first_name -> List[Tuple[last_name, id]]
        # names = {}
        # for p in members:
        #     names.setdefault(p, [])
        #     names[p.first_name].append((actual_last_name(p.last_name), p.id))
        #
        # # Compute last name abbreviations
        # for v in names.values():
        #
        #
        #
        # # Construct dictionary with id -> name with optional letter
        # by_id = {}
        # for p in members:
        #     last_names = names[p.first_name]
        #     if len(last_names) >= 2:
        #
        # by_first_name = {name[0]: () for id, name in names.items()}
        # double_names = Person.objects.filter_members().values('first_name').annotate(
        #     name_count=Count('first_name')).values('first_name').order_by().filter(name_count__gt=1)
        # double_name_people = Person.objects.filter(first_name__in=double_names)
        #
        # double_names = Person.objects
        context.update({
            'groups': QGroup.objects.order_by('name'),
        })
        return context
