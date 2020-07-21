from collections import namedtuple
from datetime import date
from decimal import Decimal
from typing import Dict, List

from xlsxwriter import Workbook

from members.models import Person
from pennotools.qrekening.wb import write_sheet

# Exception on the contribution fee for a certain group.
ContributionException = namedtuple("ContributionException", ["group", "student", "non_student"])

contributie_header = [
    'cn',
    'Amount',
    'Bankrekening'
]


def get_contributie_row(p: Person, value: Decimal) -> Dict:
    return {
        'cn': '{} {}'.format(p.first_name, p.last_name),
        'Amount': value,
        'Bankrekening': p.iban
    }


def get_contribution_fee(person: Person,
                         student: Decimal,
                         non_student: Decimal,
                         exceptions: List[ContributionException]) -> Decimal:
    """Returns the contribution fee for this person.

    Checks for group exceptions and whether the person is a student or not.
    """
    # Filter exceptions for those that apply
    applicable_exceptions = [x for x in exceptions if person.groups.filter(pk=x.group.pk).exists()]
    if applicable_exceptions:
        if person.is_student:
            fees = [x.student for x in applicable_exceptions]
        else:
            fees = [x.non_student for x in applicable_exceptions]
        return min(fees)
    return student if person.is_student else non_student


def get_contributie(student: Decimal, non_student: Decimal, admin: Decimal, exceptions: List[ContributionException]):
    """Get rows of contributie document.

    Returns:
        tuple (debtors, debtors_self), where each tuple
        element is a list of rows. Each row is a dictionary of header->value.
    """
    debtors, debtors_self = [], []
    # Only include current members
    for person in Person.objects.filter_members():
        value = get_contribution_fee(person, student, non_student, exceptions)

        if has_sepa(person):
            debtors.append(get_contributie_row(person, value))
        else:
            debtors_self.append(get_contributie_row(person, value + admin))
    return debtors, debtors_self


def write_contributie(workbook: Workbook,
                      student: Decimal,
                      non_student: Decimal,
                      admin: Decimal,
                      exceptions: List[ContributionException]):
    """Writes contribution rows into a workbook."""
    debtors, debtors_self = get_contributie(student, non_student, admin, exceptions)
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


def get_sepa_rows(p: Person, value: Decimal, description, split=Decimal('100.00')) -> List[Dict]:
    """Get SEPA rows for a person.

    Args:
        p: -
        value: -
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


def get_contributie_sepa(student: Decimal,
                         non_student: Decimal,
                         exceptions: List[ContributionException],
                         description=sepa_default_description) -> List[Dict]:
    """Gets SEPA rows for Davilex people.

    Args:
        student: -
        non_student: -
        exceptions: -
        description: Description used for the SEPA rows. Can be a string or a
            callable which returns a string.
    """
    rows = []
    # Only include members
    for person in Person.objects.filter_members():
        value = get_contribution_fee(person, student, non_student, exceptions)

        if not has_sepa(person):
            pass
        else:
            rows += get_sepa_rows(person, value, description=description)
    return rows


def write_contributie_sepa(workbook: Workbook,
                           student: Decimal,
                           non_student: Decimal,
                           exceptions: List[ContributionException]):
    """Gets SEPA rows and writes them in the workbook."""
    write_sheet(workbook, 'Debiteuren', sepa_header, get_contributie_sepa(student, non_student, exceptions))


def has_sepa(person: Person):
    """Returns whether the person has a SEPA mandate."""
    # When someone has sepa_direct_debit=True and not iban, then that's an error in the members database
    return person.sepa_direct_debit and person.iban
