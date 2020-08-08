from django import template

register = template.Library()


@register.filter
def iban(value):
    """IBAN formatting using groups of 4."""
    # Shameless copy from localflavor/generic/forms.py
    if value is None:
        return value
    grouping = 4
    value = value.upper().replace(' ', '').replace('-', '')
    return ' '.join(value[i:i + grouping] for i in range(0, len(value), grouping))
