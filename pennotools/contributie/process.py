from members.models import Person, GroupMembership
from pennotools.qrekening.wb import write_sheet
from typing import Dict
from xlsxwriter import Workbook


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


def get_contributie(base: int, admin: int, filters: Dict):
    """Get rows of contributie document.

    Returns:
        tuple (debtors, debtors_self), where each tuple
        element is a list of rows. Each row is a dictionary of header->value.
    """
    debtors, debtors_self = [], []
    for person in Person.objects.all():
        value = base
        """"Compare person to group filters"""
        for group, val in filters.items():
            for membership in GroupMembership.objects.filter(user=person):
                if int(group) == membership.group.id and int(val) < value:
                    value = int(val)

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

