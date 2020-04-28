from typing import Dict, List

from xlrd import Book, xldate_as_datetime
from xlsxwriter import Workbook

from pennotools.qrekening.process import get_qrekening, qrekening_header, sepa_header, get_sepa
from pennotools.qrekening.qperson import DavilexPerson


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
                row[name.value] = value
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
                current_person.add_boekstuk(
                    debet,
                    row['Openstaand'],
                    xldate_as_datetime(row['Fac/Bet Datum'], 0),  # 1900-based datemode
                    row['Omschrijving'].strip(),
                    # Todo: Wessel ik heb deze strip toegevoegd voor de 4 spaties voorop, is dat okay?
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
            s.write(row_nr, i, row[header[i]])
        row_nr += 1


def write_qrekening(dav_people, workbook: Workbook):
    """Get Q-rekening and write it in the workbook."""
    creditors, debtors, debtors_self, external = get_qrekening(dav_people)
    write_sheet(workbook, 'Crediteuren', qrekening_header, creditors)
    write_sheet(workbook, 'Debiteuren', qrekening_header, debtors)
    write_sheet(workbook, 'DebiteurenZelf', qrekening_header, debtors_self)
    write_sheet(workbook, 'Externen', qrekening_header, external)


def write_sepa(dav_people, workbook: Workbook):
    """Get SEPA rows and write in the workbook."""
    write_sheet(workbook, 'Debiteuren', sepa_header, get_sepa(dav_people))
