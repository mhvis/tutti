"""Utility functions for graphing using matplotlib."""

from base64 import b64encode
from collections import Counter
from io import BytesIO
from typing import Iterable

from matplotlib.axes import Axes
from matplotlib.figure import Figure

import numpy as np
from matplotlib.ticker import MaxNLocator


def render_data_url(fig: Figure, format='svg') -> str:
    """Renders a figure as a base64 encoded data URL for use in img.

    Args:
        fig: The Matplotlib figure.
        format: The format, can be either svg or png.
    """
    urls = {
        'svg': 'data:image/svg+xml;base64,{}',
        'png': 'data:image/png;base64,{}',
    }
    buf = BytesIO()
    fig.savefig(buf, format=format)
    encoded = b64encode(buf.getbuffer()).decode('ascii')
    return urls[format].format(encoded)


def pie(x, labels, title: str = None) -> str:
    """Constructs a pie chart from a list of values and labels.

    See matplotlib.pyplot.pie.
    """
    fig = Figure()
    ax = fig.subplots()  # type: Axes
    total = sum(x)
    ax.pie(x, labels=labels, shadow=True, autopct=lambda p: '{:.0f}'.format(p * total / 100))
    ax.axis('equal')
    if title:
        ax.set_title(title)
    return render_data_url(fig)


def date_plot(dates, values, title=None, from_zero=False):
    """Plot with dates on the x-axis."""
    fig = Figure()
    ax = fig.subplots()  # type: Axes
    ax.plot(dates, values)
    if from_zero:
        # Start y-axis at 0
        ax.set_ylim(ymin=0)
    fig.autofmt_xdate()
    if title:
        ax.set_title(title)
    return render_data_url(fig)


def hist(x, bins=None, range=None, title=None):
    """Histogram plot, see matplotlib.pyplot.hist."""
    fig = Figure()
    ax = fig.subplots()  # type: Axes
    ax.hist(x, bins=bins, range=range)
    if title:
        ax.set_title(title)
    return render_data_url(fig)


def bar(labels, values, title=None):
    """Bar plot, see matplotlib.pyplot.bar."""
    fig = Figure()
    ax = fig.subplots()  # type: Axes
    # x_pos = np.arange(len(labels))
    ax.bar(labels, values)
    # ax.set_xticks(x_pos)
    # ax.set_xticklabels(labels)
    ax.set_yticks(range(max(values) + 1))
    if title:
        ax.set_title(title)
    return render_data_url(fig)


def count_bar(values: Iterable[int], title=None):
    """Bar plot where each bar is a count of the occurrence in a list.

    The list must be of integers.
    """
    fig = Figure()
    ax = fig.subplots()  # type: Axes
    counter = Counter(values)
    x_arr = np.arange(min(values), max(values) + 1)
    y_arr = np.array([counter[x] for x in x_arr])
    ax.bar(x_arr, y_arr)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))  # Force integer ticks
    if title:
        ax.set_title(title)
    return render_data_url(fig)
