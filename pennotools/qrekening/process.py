from datetime import date
from decimal import Decimal
from typing import Dict, List

from members.models import Person
from pennotools.qrekening.qperson import DavilexPerson


def combine_persons(davilex_people: Dict[str, DavilexPerson]):
    """Link a Person to a DavilexPerson."""
    for davilex_person in davilex_people.values():
        try:
            person = Person.objects.get(person_id=davilex_person.id)
            davilex_person.add_person(person)
        except Person.DoesNotExist:
            pass


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


def get_qrekening_row(p: DavilexPerson) -> Dict:
    return {
        'StuurStatus': '',
        'CODE': p.id,
        'Naam': p.name,
        'Opmerkingen': '',
        'Email': p.get_email() or 'None',  # When e-mail is empty, put down 'None'
        'Bankreknr': p.get_iban(),
        'Deb Tot Open': p.get_debet_total(),
        'Deb Omschrijving': p.get_debet_description(),
        'Deb Datum': p.get_debet_dates(),
        'Deb Bedrag': p.get_debet_amounts(),
        'Deb Open': p.get_debet_amounts(),
        'Cred Tot Open': p.get_credit_total(),
        'Cred Omschrijving': p.get_credit_description(),
        'Cred Datum': p.get_credit_dates(),
        'Cred Bedrag': p.get_credit_amounts(),
        'Cred Open': p.get_credit_amounts(),
        'Totaal Open Tekst': str(p.get_total().quantize(Decimal('0.01'))),
        'Totaal Open Temp': p.get_total(),
    }


def get_qrekening(dav_people: Dict[str, DavilexPerson]):
    """Get rows of Q-rekening document.

    Returns:
        4-tuple (creditors, debtors, debtors_self, external), where each tuple
        element is a list of rows. Each row is a dictionary of header->value.
    """
    creditors, debtors, debtors_self, external = [], [], [], []
    for p in dav_people.values():
        row = get_qrekening_row(p)
        # Is this person from Q?
        if p.q_person:
            if p.get_total() < 0:
                creditors.append(row)
            elif not p.get_iban() or not p.q_person.sepa_direct_debit:
                debtors_self.append(row)
            else:
                debtors.append(row)
        else:
            external.append(row)
    return creditors, debtors, debtors_self, external


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

# Refer to https://www.rabobank.nl/images/pdf_formaatbeschrijving_csv_29856100.pdf
rabo_sepa_header = ['Kenmerk machtiging',
                    'Naam betaler',
                    'Verkorte naam',
                    'Rekeningnummer',
                    'Rekeninggroep',
                    'Bedrag',
                    'Valuta',
                    'Categorie',
                    'Landcode',
                    'Omschrijving 1',
                    'Omschrijving 2',
                    'Omschrijving 3',
                    'Type machtiging',
                    'Ondertekend op'
                    ]


def get_sepa_rows(p: DavilexPerson, description, split=Decimal('130.00'), kenmerk: str = '') -> List[Dict]:
    """Get SEPA rows for a person.

    Args:
        p: Person.
        description: Description which is included in the SEPA rows. Can be a
            string or a callable which returns a string.
        split: Amount is split over multiple rows if it is higher than this.
        kenmerk: Mandaat kenmerk.
    """
    rows = []
    #
    # def get_row(amount):
    #     return {
    #         'IBAN': p.get_iban(),
    #         'BIC': '',
    #         'mandaatid': p.id,
    #         'mandaatdatum': '',
    #         'bedrag': amount,
    #         'naam': p.name,
    #         'beschrijving': description() if callable(description) else description,
    #         'endtoendid': '{}{}'.format(p.id, date.today().strftime('%m%y')),
    #     }

    def get_rabo_row(amount):
        return {
            'Kenmerk machtiging': kenmerk,
            'Naam betaler': p.name,
            'Verkorte naam': p.id,
            'Rekeningnummer': p.get_iban(),
            'Rekeninggroep': 'Algemeen',
            'Bedrag': f'{amount:.2f}'.replace('.', ','),
            'Valuta': 'EUR',
            'Categorie': '',
            'Landcode': p.get_iban()[:2],
            'Omschrijving 1': description() if callable(description) else description,
            'Omschrijving 2': '',
            'Omschrijving 3': '',
            'Type machtiging': 'Doorlopend',
            'Ondertekend op': p.q_person.get_sepa_sign_date(),
        }

    total = p.get_total()
    while total > split:
        rows.append(get_rabo_row(amount=split))
        total -= split
    rows.append(get_rabo_row(amount=total))
    return rows


def sepa_default_description():
    return 'Qrekening {}'.format(date.today().strftime('%B %Y'))


def get_sepa(dav_people: Dict[str, DavilexPerson], description=sepa_default_description, kenmerk='') -> List[Dict]:
    """Get SEPA rows for Davilex people.

    Args:
        dav_people: Davilex people.
        description: Description used for the SEPA rows. Can be a string or a
            callable which returns a string.
        kenmerk: Mandaat kenmerk.
    """
    rows = []
    for p in dav_people.values():
        if p.q_person:
            print(f'Q person: {p.name}')
            if p.get_total() < 0 or not p.get_iban() or not p.q_person.sepa_direct_debit:
                pass
            else:
                rows += get_sepa_rows(p, description=description, kenmerk=kenmerk)
    return rows
