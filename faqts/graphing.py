"""Utility functions for graphing using matplotlib."""

from base64 import b64encode
from io import BytesIO
from typing import List, Iterable

from matplotlib.axes import Axes
from matplotlib.dates import date2num
from matplotlib.figure import Figure

import numpy as np

from members.models import QGroup


def base64png(fig: Figure) -> str:
    """Renders a figure as a base64 encoded PNG."""
    buf = BytesIO()
    fig.savefig(buf, format='png')
    return b64encode(buf.getbuffer()).decode('ascii')


def pie(x: Iterable[int], labels: Iterable[str]) -> str:
    """Constructs a pie chart from a list of values and labels."""
    fig = Figure()
    ax = fig.subplots()  # type: Axes
    total = sum(x)
    ax.pie(x, labels=labels, shadow=True, autopct=lambda p: '{:.0f}'.format(p * total / 100))
    return base64png(fig)


def group_membership_counts(g: QGroup):

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

    # Convert delta values to cumulative values
    cumulative = np.cumsum(deltas)
    return dates, cumulative


def date_plot(dates, values):
    """Plot with dates on the x-axis."""
    fig = Figure()
    ax = fig.subplots()  # type: Axes

    ax.plot(dates, values)
    fig.autofmt_xdate()
    return base64png(fig)
