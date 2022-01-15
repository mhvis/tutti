import logging
from typing import Dict, List

from xlsxwriter import Workbook

logger = logging.getLogger(__name__)


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
