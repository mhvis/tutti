import logging
from decimal import Decimal
from typing import Dict, List

from xlrd import Book, xldate_as_datetime
from xlsxwriter import Workbook

from pennotools.qrekening.davilex import DavilexAccount
from pennotools.qrekening.process import get_qrekening, qrekening_header
from pennotools.qrekening.qperson import DavilexPerson

logger = logging.getLogger(__name__)


def iterate_rows(wb: Book):
    """Iterates all rows in all workbook sheets, using first row as header.

    Yields:
        Each non-header row, as a dictionary of header key to value.
    """
    for s in wb.sheets():
        col_names = s.row(0)
        for row_nr in range(1, s.nrows):
            row = {}
            for name, col_nr in zip(col_names, range(s.ncols)):
                value = s.cell(row_nr, col_nr).value
                header: str = name.value
                # Check for similar 'omschrijving' headers
                if 'omschrijving' in header.lower():
                    header = 'Omschrijving'
                row[header] = value
            yield row


def read_exc(wb: Book, debet: bool, persons: Dict[str, DavilexPerson]) -> Dict[str, DavilexPerson]:
    """Reads the given workbook and returns DavilexPerson instances.

    - Input: | sheet: a string of the path to the excel sheet
             | debet: boolean whether it is debet (true) or credit (false)
             | persons: dict (qID:DavilexPerson)

    Raises:
        ValueError: When input workbook is invalid.
    """
    try:
        current_person = None
        for row in iterate_rows(wb):
            logger.debug("Row: %s", row)
            if current_person is None:
                # Not at person boekstuk rows
                if row['Zoekcode'] and row['Omschrijving']:
                    current_person = persons.setdefault(row['Zoekcode'],
                                                        DavilexPerson(row['Omschrijving'], row['Zoekcode']))
            elif row['Zoekcode'] != '' and 'totaal' in row['Omschrijving']:
                # Ending person
                current_person = None
            else:
                # Person boekstuk row
                #
                # Amount is converted from float to Decimal (exactness of
                # Decimal is better for money values).
                #
                # Note: the value is rounded to 2 decimal places, this should
                # always yield the same value as the original float.
                logger.debug("Openstaand float: %s", row['Openstaand'])
                amount = Decimal(row['Openstaand']).quantize(Decimal('1.00'))
                logger.debug("Openstaand decimal: %s", amount)

                current_person.add_boekstuk(
                    debet,
                    amount,
                    xldate_as_datetime(row['Fac/Bet Datum'], 0),  # 1900-based datemode
                    row['Omschrijving'].strip(),
                )
    except KeyError as e:
        # KeyError is raised when an invalid header is encountered
        raise ValueError("Invalid header: {}".format(e))
    return persons


def write_sheet(workbook: Workbook, sheet_name: str, header: List[str], rows: List[Dict]):
    """Write given header and rows in a workbook sheet."""
    s = workbook.add_worksheet(sheet_name)
    s.set_column(0, len(header) - 1, width=10)  # Some arbitrary width for the columns

    # Write header
    for i in range(len(header)):
        s.write(0, i, header[i])

    # Write rows
    row_nr = 1
    for row in rows:
        for i in range(len(header)):
            # Note, from the xlsxwriter docs:
            #
            # "When written to an Excel file numbers are converted to IEEE-754 64-bit double-precision floating point.
            # This means that, in most cases, the maximum number of digits that can be stored in Excel without losing
            # precision is 15."
            s.write(row_nr, i, row[header[i]])
        row_nr += 1
