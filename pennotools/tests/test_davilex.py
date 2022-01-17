from datetime import date
from decimal import Decimal

from django.test import TestCase

from pennotools.core.davilex import parse_amount, parse_davilex_report, DavilexBook, DavilexJournalEntry

# flake8: noqa

s1 = """Boekstukvolgnr	Zoekcode	Omschrijving verkoopboekstuk	Factuurnr	Fac/Bet Datum	Vervaldatum	Bedrag	Betaling	Openstaand	
									
									
	JOHBAC	Johann Sebastian Bach							
255		     Repetitieweekend ledenbijdrage		13-11-2021		€ 42,05		€ 42,05	
338		     Drank repetitieweekend		14-11-2021		€ 0,60		€ 0,60	
388		     AQCie		18-11-2021		€ 5,00		€ 5,00	
398		     Bestuursfoto's 		9-12-2021		€ 4,38		€ 4,38	
	JOHBAC	Johann Sebastian Bach totaal				€ 52,03	€ 0,00	€ 52,03	
									
	FRASCH	Franz Schubert							
123		     Parkeervergoeding		13-11-2021		€ 1.234,56	€ 1.224,56	€ 10,00	
	FRASCH	Franz Schubert totaal				€ 1.234,56	€ 1.224,56	€ 10,00	
									
	ONB	Niemand							
	ONB	Niemand totaal				€ 0,00	€ 0,00	€ 0,00	
									
		TOTAAL				€ 1.286,59	€ 1.224,56	€ 62,03	
"""


class DavilexTestCase(TestCase):
    def test_parse_amount(self):
        self.assertEqual(Decimal('42.05'), parse_amount('€ 42,05'))
        self.assertEqual(Decimal('0.00'), parse_amount('€ 0,00'))
        self.assertEqual(Decimal('100000000000.00'), parse_amount('€ 100.000.000.000,00'))
        with self.assertRaises(ValueError):
            parse_amount('')

    def test_parse_davilex(self):
        expect = [
            DavilexBook(search_code='JOHBAC', description='Johann Sebastian Bach', entries=[
                DavilexJournalEntry(entry_no=255, description='Repetitieweekend ledenbijdrage', date=date(2021, 11, 13),
                                    amount=Decimal('42.05'), paid=Decimal('0.00'), open=Decimal('42.05')),
                DavilexJournalEntry(entry_no=338, description='Drank repetitieweekend', date=date(2021, 11, 14),
                                    amount=Decimal('0.60'), paid=Decimal('0.00'), open=Decimal('0.60')),
                DavilexJournalEntry(entry_no=388, description='AQCie', date=date(2021, 11, 18), amount=Decimal('5.00'),
                                    paid=Decimal('0.00'), open=Decimal('5.00')),
                DavilexJournalEntry(entry_no=398, description="Bestuursfoto's", date=date(2021, 12, 9),
                                    amount=Decimal('4.38'), paid=Decimal('0.00'), open=Decimal('4.38')),
            ]),
            DavilexBook(search_code='FRASCH', description='Franz Schubert', entries=[
                DavilexJournalEntry(entry_no=123, description='Parkeervergoeding', date=date(2021, 11, 13),
                                    amount=Decimal('1234.56'), paid=Decimal('1224.56'), open=Decimal('10.00'))
            ]),
            DavilexBook(search_code='ONB', description='Niemand', entries=[]),
        ]
        self.assertEqual(expect, parse_davilex_report(s1))
