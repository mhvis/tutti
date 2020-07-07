from members.models import Person
from pennotools.qrekening.wb import write_sheet
from typing import Dict


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


def get_contributie():
    """Get rows of contributie document.

    Returns:
        4-tuple (creditors, debtors, debtors_self, external), where each tuple
        element is a list of rows. Each row is a dictionary of header->value.
    """
    debtors, debtors_self = [], []
    for person in Person.objects.all():
        if person.sepa_direct_debit:
            if person.is_student:
                debtors.append(get_contributie_row(person, 60))
            else:
                debtors.append(get_contributie_row(person, 120))
        else:
            if person.is_student:
                debtors_self.append(get_contributie_row(person, 66))
            else:
                debtors_self.append(get_contributie_row(person, 126))
    return debtors, debtors_self


def write_contributie(workbook):
    debtors, debtors_self = get_contributie()
    write_sheet(workbook, 'Debiteuren', contributie_header, debtors)
    write_sheet(workbook, 'DebiteurenZelf', contributie_header, debtors_self)

