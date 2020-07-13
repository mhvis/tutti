from members.models import Person, GroupMembership
from pennotools.qrekening.wb import write_sheet
from typing import Dict, List
from decimal import Decimal
from xlsxwriter import Workbook
from datetime import date


contributie_header = [
    'cn',
    'Amount',
    'Bankrekening'
]

def get_contributie_row(p: Person, value: int) -> Dict:
    return {
        'cn': '{} {}'.format(p.first_name, p.last_name),
        'Amount': value,
        'Bankrekening': p.iban
    }

def get_filtered_value(person, base, filters):
    """"Compare person to group filters"""
    value = base
    for group, val in filters.items():
        for membership in GroupMembership.objects.filter(user=person):
            if int(group) == membership.group.id and int(val) < value:
                value = int(val)
    return value


def get_contributie(base: int, admin: int, filters: Dict):
    """Get rows of contributie document.

    Returns:
        tuple (debtors, debtors_self), where each tuple
        element is a list of rows. Each row is a dictionary of header->value.
    """
    debtors, debtors_self = [], []
    for person in Person.objects.all():
        value = get_filtered_value(person, base, filters)

        """"Double value if person is not a student"""
        value = value if person.is_student else value * 2
        if person.sepa_direct_debit:
            debtors.append(get_contributie_row(person, value))
        else:
            debtors_self.append(get_contributie_row(person, value + admin))
    return debtors, debtors_self


def write_contributie(workbook: Workbook, base: int, admin: int, filters: Dict):
    debtors, debtors_self = get_contributie(base, admin, filters)
    write_sheet(workbook, 'Debiteuren', contributie_header, debtors)
    write_sheet(workbook, 'DebiteurenZelf', contributie_header, debtors_self)

# SEPA

sepa_header = ['IBAN',
               'BIC',
               'mandaatid',
               'mandaatdatum',
               'bedrag',
               'naam',
               'beschrijving',
               'endtoendid'
               ]


def get_sepa_rows(p: Person, value: int, description, split=Decimal('100.00')) -> List[Dict]:
    """Get SEPA rows for a person.

    Args:
        p: Person.
        value: int.
        description: Description which is included in the SEPA rows. Can be a
            string or a callable which returns a string.
        split: Amount is split over multiple rows if it is higher than this.

    """
    rows = []

    def get_row(amount):
        return {
            'IBAN': p.iban,
            'BIC': '',
            'mandaatid': p.person_id,
            'mandaatdatum': '',
            'bedrag': amount,
            'naam': "{} {}".format(p.first_name, p.last_name),
            'beschrijving': description() if callable(description) else description,
            'endtoendid': '{}{}'.format(p.person_id, date.today().strftime('%Y')),
        }

    total = value
    while total > split:
        rows.append(get_row(amount=split))
        total -= split
    rows.append(get_row(amount=total))
    return rows


def sepa_default_description():
    return 'Contributie {}'.format(date.today().strftime('%Y'))


def get_contributie_sepa(base: int, filters: int, description=sepa_default_description) -> List[Dict]:
    """Get SEPA rows for Davilex people.

    Args:
        dav_people: Davilex people.
        description: Description used for the SEPA rows. Can be a string or a
            callable which returns a string.
    """
    rows = []
    for person in Person.objects.all():
        value = get_filtered_value(person, base, filters)

        """"Double value if person is not a student"""
        value = value if person.is_student else value * 2
        if not person.iban or not person.sepa_direct_debit:
            pass
        else:
            rows += get_sepa_rows(person, value, description=description)
    print(rows)
    return rows

def write_contributie_sepa(workbook: Workbook, base: int, filters: int):
    """Get SEPA rows and write in the workbook."""
    write_sheet(workbook, 'Debiteuren', sepa_header, get_contributie_sepa(base, filters))
