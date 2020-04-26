import os
from datetime import datetime

import xlrd
from django.test import TestCase

from pennotools.qrekening.qperson import DavilexPerson
from pennotools.qrekening.wb import read_exc


class QRekeningTestCase(TestCase):
    def test_read_exc(self):
        filename = os.path.join(os.path.dirname(__file__), 'qrekening/testfile_read.xlsx')
        wb = xlrd.open_workbook(filename)

        # Expected result
        johbac = DavilexPerson('Johann Sebastian Bach', 'JOHBAC')
        johbac.add_boekstuk(True, 400.0, datetime(2020, 10, 7), 'Partita score')
        johbac.add_boekstuk(True, 60.0, datetime(2016, 10, 7), 'Organ repair')
        nicpag = DavilexPerson('Niccolo Paganini', 'NICPAG')
        nicpag.add_boekstuk(True, 10000.0, datetime(2002, 11, 28), 'Stradivarius violin')  # Good value
        devil = DavilexPerson('The Devil', 'DEVIL')
        devil.add_boekstuk(True, 100000000000.0, datetime(2012, 11, 28), 'Soul of Paganini')
        expect = {
            'JOHBAC': johbac,
            'NICPAG': nicpag,
            'DEVIL': devil,
        }

        actual = read_exc(wb, True, {})
        self.assertEqual(expect, actual)
