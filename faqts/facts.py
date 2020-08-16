"""Utility functions that compute summaries about the members data."""
from typing import Tuple, List

from django.db.models import Q, Count

from members.models import Instrument, Person, QGroup

import numpy as np


def instrument_counts(cutoff=0) -> List[Tuple[str, int]]:
    """Computes total number of each instrument played amongst the members.

    Args:
        cutoff: Counts less than or equal to cutoff are summed and the
            instruments are discarded.

    Returns:
        A list of instrument name+count pairs. If the cutoff count is non-zero,
            it is the last item in the list with a name of 'Other'. The other
            items are sorted alphabetically.
    """
    # Get counts
    members = Person.objects.filter_members()
    counts = Instrument.objects.all().annotate(num_people=Count('person', filter=Q(person__in=members)))
    # Exclude instruments that have a count of 0
    counts = counts.filter(num_people__gt=0)
    # Order by instrument name
    counts = counts.order_by('name')
    # print(counts.explain())
    result = [(i.name.capitalize(), i.num_people) for i in counts]

    # Discard and sum instrument counts that are <= cutoff.
    filtered = []
    leftover = 0
    for t in result:
        if t[1] <= cutoff:
            leftover += t[1]
        else:
            filtered.append(t)
    if leftover > 0:
        filtered.append(("Other", leftover))
    return filtered


def group_size_curve(g: QGroup):
    """Calculates a graph with group size over time for given group.

    Returns:
        Two NumPy arrays for the x and y axis. The x axis is a list of dates,
            the y axis is a list of group size for that date.
    """
    # Get delta values of the change in group memberships at given dates
    dates = []
    deltas = []
    for m in g.groupmembership_set.all():
        dates.append(m.start)
        deltas.append(1)
        if m.end:
            dates.append(m.end)
            deltas.append(-1)

    dates = np.array(dates)
    deltas = np.array(deltas)

    # Sort on date
    sorted_indices = dates.argsort()
    dates = dates[sorted_indices]
    deltas = deltas[sorted_indices]

    # Do some magic which I don't understand
    # (But this person does: https://stackoverflow.com/a/55736036)
    # This sums deltas that are on the same date
    binned_dates, inv = np.unique(dates, return_inverse=True)
    binned_deltas = np.zeros(len(binned_dates), dtype=deltas.dtype)
    np.add.at(binned_deltas, inv, deltas)

    # Convert delta values to cumulative values
    cumulative = np.cumsum(binned_deltas)
    return binned_dates, cumulative
