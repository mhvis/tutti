from datetime import datetime, timezone
from typing import List

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views.generic import TemplateView

from faqts.facts import instrument_counts, group_size_curve
from faqts.graphing import pie, date_plot, bar, count_bar
from members.models import QGroup, Person, GroupMembership


class FaQtsView(LoginRequiredMixin, TemplateView):
    template_name = "faqts/faqts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        members = Person.objects.filter_members()  # Filter members

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
        birth_years = list(members.filter(date_of_birth__isnull=False).values_list('date_of_birth__year', flat=True))
        context['birth_year_plot'] = count_bar(birth_years, title="Birth years")

        # Length of Q membership
        membership_starts = list(GroupMembership.objects.filter(group=settings.MEMBERS_GROUP,
                                                                end=None).values_list('start__year', flat=True))
        context['membership_start_plot'] = count_bar(membership_starts,
                                                     title="Membership start years")

        # Triplegänger
        triple_name_qs = members.values('first_name').annotate(name_count=Count('first_name')).filter(
            name_count__gte=3).values_list('first_name', 'name_count')
        context['triples_plot'] = bar(*zip(*triple_name_qs),
                                      title="Triplegänger")

        return context


class GroupsView(TemplateView):
    template_name = 'faqts/groups.html'

    def get_context_data(self, **kwargs):  # noqa: C901
        """Ugly monster method for computing last name abbreviations."""
        context = super().get_context_data(**kwargs)

        def actual_last_name(last_name: str) -> str:
            """Gets rid of 'van'/'de'/... by cutting until the first capital."""
            first_capital_idx = 0
            for i in range(len(last_name)):
                if last_name[i].isupper():
                    first_capital_idx = i
                    break
            return last_name[first_capital_idx:]

        def abbreviate(names: List[str]) -> List[str]:
            """Computes abbreviations for a list of (last) names.

            The list must have a least 2 names.

            If some names start with the same letter(s), the abbreviation will
            be made longer, to be able to differentiate between those.
            """
            if len(names) < 2:
                raise ValueError
            result = []
            for name in names:
                abbreviation = None
                # Increase the number of characters until no clashes are found
                for i in range(len(name)):
                    clashes = sum([s.lower().startswith(name.lower()[:i + 1]) for s in names])
                    # There will always be at least 1 clash, namely with itself
                    if clashes == 1:
                        abbreviation = "{}.".format(name[:i + 1])
                        break
                result.append(abbreviation or name)  # If abbreviation was None, use the full name
            return result

        # Compute double name abbreviations

        # Django ORM turned out to be a bit annoying (https://stackoverflow.com/q/8989221) so I changed it by fetching
        #  all data and doing it in-memory.

        # Construct dictionary with first_name -> List[Tuple[last_name, id]]
        names = {}
        for p in Person.objects.filter_members():
            names.setdefault(p.first_name, [])
            names[p.first_name].append((actual_last_name(p.last_name), p.id))

        # Construct dictionary with id -> display name, where display name has a last name abbreviation if necessary
        display_name = {}
        for first_name, v in names.items():
            if len(v) == 1:
                # No abbreviation necessary
                display_name[v[0][1]] = first_name
            else:
                # Abbreviate the last names and update the display name dictionary
                last_names, ids = zip(*v)  # Unzip
                abbr = abbreviate(last_names)
                display_names = ["{} {}".format(first_name, a) for a in abbr]
                display_name.update({t[0]: t[1] for t in zip(ids, display_names)})

        # Gather groups by category
        a = QGroup.objects.filter(show_in_overview=True).order_by('name')
        b = {
            'committee': a.filter(category='committee'),
            'ensemble': a.filter(category='ensemble'),
            'subassociation': a.filter(category='subassociation'),
            # If a new category is added it will not automatically display on this page
            'other': a.filter(category=''),
        }

        # Create dictionary with category -> list of groups
        groups = {}
        for cat, group_qs in b.items():
            groups[cat] = [{
                'name': g.name,
                'description': g.description,
                # The display name dictionary only includes Q members while some groups might also have non-members.
                # Just use first name in those cases.
                'people': sorted([display_name.get(u.id, u.first_name) for u in g.user_set.all()])
            } for g in group_qs]

        context.update({
            'groups': groups,
        })
        return context
