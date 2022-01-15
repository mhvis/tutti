import logging
from decimal import Decimal
from typing import Dict, List, Tuple

from members.models import Person
from pennotools.core.davilex import DavilexAccount

logger = logging.getLogger(__name__)

# Q-rekening

qrekening_header = ['StuurStatus',
                    'CODE',
                    'Naam',
                    'Opmerkingen',
                    'Email',
                    'Bankreknr',
                    'Deb Tot Open',
                    'Deb Omschrijving',
                    'Deb Datum',
                    'Deb Bedrag',
                    'Deb Open',
                    'Cred Tot Open',
                    'Cred Omschrijving',
                    'Cred Datum',
                    'Cred Bedrag',
                    'Cred Open',
                    'Totaal Open Tekst',
                    'Totaal Open Temp'
                    ]


def get_qrekening_row(p: DavilexAccount) -> Dict:
    return {
        'StuurStatus': '',
        'CODE': p.search_code,
        'Naam': p.description,
        'Opmerkingen': '',
        'Email': p.get_email() or 'None',  # When e-mail is empty, put down 'None'
        'Bankreknr': p.get_iban(),
        'Deb Tot Open': str(p.get_open_debit()),
        'Deb Omschrijving': '\n'.join(d.description for d in p.debit),
        'Deb Datum': '\n'.join(d.date.strftime("%d-%m-%Y") for d in p.debit),
        'Deb Bedrag': '\n'.join(str(d.open) for d in p.debit),
        'Deb Open': '\n'.join(str(d.open) for d in p.debit),
        'Cred Tot Open': str(p.get_open_credit()),
        'Cred Omschrijving': '\n'.join(c.description for c in p.credit),
        'Cred Datum': '\n'.join(c.date.strftime("%d-%m-%Y") for c in p.credit),
        'Cred Bedrag': '\n'.join(str(c.open) for c in p.credit),
        'Cred Open': '\n'.join(str(c.open) for c in p.credit),
        'Totaal Open Tekst': str(p.get_total_open()),
        'Totaal Open Temp': p.get_total_open(),
    }


def get_qrekening(accounts: List[DavilexAccount]):
    """Get rows of Q-rekening document.

    Returns:
        4-tuple (creditors, debtors, debtors_self, external), where each tuple
        element is a list of rows. Each row is a dictionary of header->value.
    """
    creditors, debtors, debtors_self, external = [], [], [], []
    for p in accounts:
        row = get_qrekening_row(p)
        # Is this person from Q?
        if p.q_person:
            if p.get_total_open() < 0:
                creditors.append(row)
            elif not p.get_iban() or not p.q_person.sepa_direct_debit:
                debtors_self.append(row)
            else:
                debtors.append(row)
        else:
            external.append(row)
    return creditors, debtors, debtors_self, external


def qrekening_sepa_amounts(accounts: List[DavilexAccount]) -> List[Tuple[Person, Decimal]]:
    """Returns the people that have SEPA direct debit, with the amount to be debited."""
    rows = []
    for p in accounts:
        # Person needs to have IBAN and direct debit, and amount must be (strictly) positive
        if p.q_person and p.q_person.iban and p.q_person.sepa_direct_debit and p.get_total_open() > 0:
            rows.append((p.q_person, p.get_total_open()))
    return rows
