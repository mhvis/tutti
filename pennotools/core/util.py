import unicodedata
from decimal import Decimal
from typing import Tuple, Iterable
from xml.etree.ElementTree import Element,tostring
from string import digits

from members.models import Person


def remove_accents(input_str):
    # From here: https://stackoverflow.com/a/517974/2373688
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def split_amount(lines: Iterable[Tuple[Person, Decimal]], split: Decimal) -> Iterable[Tuple[Person, Decimal]]:
    """Splits elements with amount greater than `split` into multiple rows."""
    for p, amount in lines:
        while amount > split:
            yield p, split
            amount -= split
        yield p, amount


def dict_to_xml(tag, d):
    elem = Element(tag)
    for key, val in d.items():
        if type(val) == dict:
            child = dict_to_xml(key, val)
        else:
            child = Element(key.lstrip(digits))
            child.text = str(val)
        elem.append(child)
    return elem
