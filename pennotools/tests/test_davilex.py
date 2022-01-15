from datetime import date
from decimal import Decimal

from django.test import TestCase

from pennotools.core.davilex import parse_amount, parse_davilex_report, DavilexBook, DavilexJournalEntry

s1 = """Boekstukvolgnr	Zoekcode	Omschrijving verkoopboekstuk	Factuurnr	Fac/Bet Datum	Vervaldatum	Bedrag	Betaling	Openstaand	
									
									
	JOHBAC	Johann Sebastian Bach							
255		     Repetitieweekend ledenbijdrage		13-11-2021		€ 42,05		€ 42,05	
338		     Drank repetitieweekend		14-11-2021		€ 0,60		€ 0,60	
388		     AQCie		18-11-2021		€ 5,00		€ 5,00	
398		     Bestuursfoto's 		9-12-2021		€ 4,38		€ 4,38	
	JOHBAC	Johann Sebastian Bach totaal				€ 52,03	€ 0,00	€ 52,03	"""


s2 = """Boekstukvolgnr	Zoekcode	Omschrijving	Factuurnr	Fac/Bet Datum	Vervaldatum	Bedrag	Betaling	Openstaand	
									
									
	JOHBAC	Johann Sebastian Bach							
192		     DECL Materiaal Intro		3-9-2021		€ 6,57		€ 6,57	
245		     DECL Q auqtion verzendkosten		13-11-2021		€ 7,25		€ 7,25	
243		     DECL Extra boodschappen repetitieweekend		13-11-2021		€ 18,96		€ 18,96	
273		     DECL Bestuurskleding		11-12-2021		€ 25,00		€ 25,00	
	JOHBAC	Johann Sebastian Bach totaal				€ 57,78	€ 0,00	€ 57,78	"""


class DavilexTestCase(TestCase):
    def test_parse_amount(self):
        self.assertEqual(Decimal('42.05'), parse_amount('€ 42,05'))
        self.assertEqual(Decimal('0.00'), parse_amount('€ 0,00'))
        self.assertEqual(Decimal('100000000000.00'), parse_amount('€ 100.000.000.000,00'))
        with self.assertRaises(RuntimeError):
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
        ]
        self.assertEqual(expect, parse_davilex_report(s1))
