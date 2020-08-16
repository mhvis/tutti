"""Utility functions for graphing using matplotlib."""

from base64 import b64encode
from io import BytesIO

from matplotlib.axes import Axes
from matplotlib.figure import Figure


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
