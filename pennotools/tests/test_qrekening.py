import os
from datetime import datetime, date
from decimal import Decimal

import xlrd
from django.test import TestCase

from members.models import Person
from pennotools.qrekening.process import combine_persons, get_qrekening, get_sepa
from pennotools.qrekening.qperson import DavilexPerson
from pennotools.qrekening.wb import read_exc


class QRekeningTestCase(TestCase):
    def test_read_exc(self):
        # Note: testfile_read.xlsx is the same as the .xls one but the new version of xlrd doesn't support .xlsx anymore
        filename = os.path.join(os.path.dirname(__file__), 'qrekening/testfile_read.xls')
        wb = xlrd.open_workbook(filename)

        # Expected result
        johbac = DavilexPerson('Johann Sebastian Bach', 'JOHBAC')
        johbac.add_boekstuk(True, Decimal('400.00'), datetime(2020, 10, 7), 'Partita score')
        johbac.add_boekstuk(True, Decimal('60.00'), datetime(2016, 10, 7), 'Organ repair')
        nicpag = DavilexPerson('Niccolo Paganini', 'NICPAG')
        nicpag.add_boekstuk(True, Decimal('9000.00'), datetime(2002, 11, 28), 'Stradivarius violin')  # Good value
        devil = DavilexPerson('The Devil', 'DEVIL')
        devil.add_boekstuk(True, Decimal('100000000000.00'), datetime(2012, 11, 28), 'Soul of Paganini')
        expect = {
            'JOHBAC': johbac,
            'NICPAG': nicpag,
            'DEVIL': devil,
        }

        actual = read_exc(wb, True, {})
        self.assertEqual(expect, actual)

    def test_combine_persons(self):
        gmahler = Person.objects.create(username='gmahler', person_id='GUSMAH')
        dav_people = {
            'GUSMAH': DavilexPerson('Gustav Mahler', 'GUSMAH')
        }
        combine_persons(dav_people)
        self.assertEqual(gmahler, dav_people['GUSMAH'].q_person)

    def test_get_qrekening(self):
        # Construct some dav_people
        johbac = DavilexPerson('Johann Sebastian Bach', 'JOHBAC')
        johbac.add_boekstuk(True, Decimal('400.00'), datetime(2020, 10, 7), 'Partita score')
        johbac.add_boekstuk(True, Decimal('60.00'), datetime(2016, 10, 7), 'Organ repair')
        johbac.add_boekstuk(False, Decimal('1000.00'), datetime(2001, 1, 2), 'Volunteer contribution')
        nicpag = DavilexPerson('Niccolo Paganini', 'NICPAG')
        nicpag.add_boekstuk(True, Decimal('10000.00'), datetime(2002, 11, 28), 'Stradivarius violin')  # Good value
        nicpag.add_boekstuk(False, Decimal('9999.99'), datetime(2002, 11, 29), 'Guarneri violin')
        devil = DavilexPerson('The Devil', 'DEVIL')
        devil.add_boekstuk(True, Decimal('100000000000.00'), datetime(2012, 11, 28), 'Soul of Paganini')
        devil.add_boekstuk(True, Decimal('5481348.54'), datetime(1910, 12, 31), 'Mozart\'s gambled money')
        dav_people = {
            'JOHBAC': johbac,
            'NICPAG': nicpag,
            'DEVIL': devil,
        }
        # Construct matching person entries
        Person.objects.create(username='jsbach', person_id='JOHBAC', iban='NL02ABNA0123456789', email='js@back.is')
        Person.objects.create(username='paganini', person_id='NICPAG')

        # Expected result
        expect = (
            [
                # Creditors
                {'StuurStatus': '', 'CODE': 'JOHBAC', 'Naam': 'Johann Sebastian Bach',
                 'Opmerkingen': '', 'Email': 'js@back.is', 'Bankreknr': 'NL02ABNA0123456789',
                 'Deb Tot Open': '460.00', 'Deb Omschrijving': 'Partita score\nOrgan repair',
                 'Deb Datum': '07-10-2020\n07-10-2016', 'Deb Bedrag': '400.00\n60.00', 'Deb Open': '400.00\n60.00',
                 'Cred Tot Open': '1000.00', 'Cred Omschrijving': 'Volunteer contribution', 'Cred Datum': '02-01-2001',
                 'Cred Bedrag': '1000.00', 'Cred Open': '1000.00', 'Totaal Open Tekst': '-540.00',
                 'Totaal Open Temp': -540}
            ],
            [
                # Debtors
            ],
            [
                # Debtors self
                {'StuurStatus': '', 'CODE': 'NICPAG', 'Naam': 'Niccolo Paganini',
                 'Opmerkingen': '', 'Email': 'None', 'Bankreknr': '',
                 'Deb Tot Open': '10000.00', 'Deb Omschrijving': 'Stradivarius violin',
                 'Deb Datum': '28-11-2002', 'Deb Bedrag': '10000.00', 'Deb Open': '10000.00',
                 'Cred Tot Open': '9999.99', 'Cred Omschrijving': 'Guarneri violin', 'Cred Datum': '29-11-2002',
                 'Cred Bedrag': '9999.99', 'Cred Open': '9999.99', 'Totaal Open Tekst': '0.01',
                 'Totaal Open Temp': Decimal('0.01')}
            ],
            [
                # External
                {'StuurStatus': '', 'CODE': 'DEVIL', 'Naam': 'The Devil',
                 'Opmerkingen': '', 'Email': 'None', 'Bankreknr': '',
                 'Deb Tot Open': '100005481348.54', 'Deb Omschrijving': 'Soul of Paganini\nMozart\'s gambled money',
                 'Deb Datum': '28-11-2012\n31-12-1910', 'Deb Bedrag': '100000000000.00\n5481348.54',
                 'Deb Open': '100000000000.00\n5481348.54',
                 'Cred Tot Open': '0.00', 'Cred Omschrijving': '', 'Cred Datum': '',
                 'Cred Bedrag': '', 'Cred Open': '', 'Totaal Open Tekst': '100005481348.54',
                 'Totaal Open Temp': Decimal('100005481348.54')}
            ]
        )

        # Run and compare
        combine_persons(dav_people)
        actual = get_qrekening(dav_people)
        self.assertEqual(expect, actual)

    def test_get_sepa(self):
        # Construct some dav_people
        johbac = DavilexPerson('Johann Sebastian Bach', 'JOHBAC')
        johbac.add_boekstuk(True, Decimal('400.00'), datetime(2020, 10, 7), 'Partita score')
        johbac.add_boekstuk(True, Decimal('60.00'), datetime(2016, 10, 7), 'Organ repair')
        johbac.add_boekstuk(False, Decimal('10.00'), datetime(2001, 1, 2), 'Volunteer contribution')
        nicpag = DavilexPerson('Niccolo Paganini', 'NICPAG')
        nicpag.add_boekstuk(True, Decimal('10000.00'), datetime(2002, 11, 28), 'Stradivarius violin')  # Good value
        nicpag.add_boekstuk(False, Decimal('9999.99'), datetime(2002, 11, 29), 'Guarneri violin')
        devil = DavilexPerson('The Devil', 'DEVIL')
        devil.add_boekstuk(True, Decimal('100000000000.00'), datetime(2012, 11, 28), 'Soul of Paganini')
        devil.add_boekstuk(True, Decimal('5481348.54'), datetime(1910, 12, 31), 'Mozart\'s gambled money')
        dav_people = {
            'JOHBAC': johbac,
            'NICPAG': nicpag,
            'DEVIL': devil,
        }
        # Construct matching person entries
        Person.objects.create(username='jsbach', person_id='JOHBAC', iban='NL02ABNA0123456789', email='js@back.is',
                              sepa_direct_debit=True)
        Person.objects.create(username='paganini', person_id='NICPAG', iban='NL02INGB0123456789',
                              sepa_direct_debit=True)

        # Expected result
        expect = [
            {'IBAN': 'NL02ABNA0123456789', 'BIC': '', 'mandaatid': 'JOHBAC', 'mandaatdatum': '', 'bedrag': 100,
             'naam': 'Johann Sebastian Bach', 'beschrijving': 'Q afschrijving',
             'endtoendid': 'JOHBAC{}'.format(date.today().strftime('%m%y'))},
            {'IBAN': 'NL02ABNA0123456789', 'BIC': '', 'mandaatid': 'JOHBAC', 'mandaatdatum': '', 'bedrag': 100,
             'naam': 'Johann Sebastian Bach', 'beschrijving': 'Q afschrijving',
             'endtoendid': 'JOHBAC{}'.format(date.today().strftime('%m%y'))},
            {'IBAN': 'NL02ABNA0123456789', 'BIC': '', 'mandaatid': 'JOHBAC', 'mandaatdatum': '', 'bedrag': 100,
             'naam': 'Johann Sebastian Bach', 'beschrijving': 'Q afschrijving',
             'endtoendid': 'JOHBAC{}'.format(date.today().strftime('%m%y'))},
            {'IBAN': 'NL02ABNA0123456789', 'BIC': '', 'mandaatid': 'JOHBAC', 'mandaatdatum': '', 'bedrag': 100,
             'naam': 'Johann Sebastian Bach', 'beschrijving': 'Q afschrijving',
             'endtoendid': 'JOHBAC{}'.format(date.today().strftime('%m%y'))},
            {'IBAN': 'NL02ABNA0123456789', 'BIC': '', 'mandaatid': 'JOHBAC', 'mandaatdatum': '', 'bedrag': 50,
             'naam': 'Johann Sebastian Bach', 'beschrijving': 'Q afschrijving',
             'endtoendid': 'JOHBAC{}'.format(date.today().strftime('%m%y'))},
            {'IBAN': 'NL02INGB0123456789', 'BIC': '', 'mandaatid': 'NICPAG', 'mandaatdatum': '',
             'bedrag': Decimal('0.01'),
             'naam': 'Niccolo Paganini', 'beschrijving': 'Q afschrijving',
             'endtoendid': 'NICPAG{}'.format(date.today().strftime('%m%y'))},
        ]

        # Run and compare
        combine_persons(dav_people)
        actual = get_sepa(dav_people, description='Q afschrijving')
        self.assertEqual(expect, actual)
