from decimal import Decimal
from typing import List, Tuple

from members.models import Person


# TODO: this snippet could be used if accents need to be removed
# import unicodedata
#
# def remove_accents(input_str):
#     nfkd_form = unicodedata.normalize('NFKD', input_str)
#     return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def rabo_sepa(lines: List[Tuple[Person, Decimal]], description: str) -> List[List[str]]:
    """Constructs table in Rabo incasso csv format.

    Format description: https://www.rabobank.nl/images/pdf_formaatbeschrijving_csv_29856100.pdf

    Args:
        lines: Each line specifies a member and the amount.
        description: See format description.

    Returns:
        A 2D table in the correct format, which can directly be saved as csv.
    """
    if len(description) > 35:
        raise ValueError("Description has maximum length of 35.")

    # Create 2D table and add header row
    csv = [['Kenmerk machtiging',
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
            ]]

    # Add rows
    for line in lines:
        p = line[0]
        amount = line[1]

        # Check that IBAN and SEPA are set
        if not p.sepa_direct_debit or not p.iban:
            raise ValueError("Person has no SEPA.")

        csv.append([
            p.person_id,  # Kenmerk
            "{} {}".format(p.first_name, p.last_name),
            p.person_id,  # Verkorte naam
            p.iban,
            'Algemeen',  # Rekeninggroep
            f'{amount:.2f}'.replace('.', ','),
            'EUR',  # Valuta
            '',  # Categorie
            p.iban[:2],  # Landcode
            description,
            '',  # Omschrijving 2
            '',  # Omschrijving 3
            'Doorlopend',  # Type machtiging
            p.get_sepa_sign_date().strftime('%d-%m-%Y'),  # Ondertekend op
        ])
    return csv
