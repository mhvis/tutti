"""Handles data input from Davilex."""
import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from typing import List

from django.utils.functional import cached_property

from members.models import Person

logger = logging.getLogger(__name__)


def parse_amount(s: str, optional=False) -> Decimal:
    """Parses amount formatted like '€ 1.252,03', the format used by Davilex.

    Args:
        s: The amount.
        optional: If True, amount may be empty, then Decimal('0.00') is returned.
    """
    # Remove € and '.', replace ',' with '.'
    s = s.replace('€', '').replace('.', '').replace(',', '.').strip()
    if not s:
        if optional:
            return Decimal('0.00')
        else:
            raise ValueError("Empty amount.")
    return Decimal(s)


@dataclass(frozen=True)
class DavilexJournalEntry:
    """Boekstuk."""
    entry_no: int  # Boekstukvolgnummer
    description: str  # Omschrijving
    date: date  # Fac/Bet Datum
    amount: Decimal  # Bedrag
    paid: Decimal  # Betaling
    open: Decimal  # Openstaand

    @classmethod
    def from_line(cls, fields: List[str]):
        # fields: Boekstukvolgnr,Zoekcode,Omschrijving,Factuurnr,Fac/Bet Datum,Vervaldatum,Bedrag,Betaling,Openstaand
        if not fields[0].strip() or not fields[2].strip() or not fields[4].strip():
            # Sanity check, some fields must exist
            raise ValueError("Invalid line format.")
        return cls(
            entry_no=int(fields[0]),
            description=fields[2].strip(),
            date=datetime.strptime(fields[4], "%d-%m-%Y").date(),
            amount=parse_amount(fields[6]),
            paid=parse_amount(fields[7], optional=True),
            open=parse_amount(fields[8]),
        )


@dataclass(frozen=True)
class DavilexBook:
    """A collection of journal entries (boekstukken) for a single book (debit or credit account)."""
    search_code: str  # Zoekcode (person ID)
    description: str  # Omschrijving (person name)
    entries: List[DavilexJournalEntry]


@dataclass
class DavilexAccount:
    """Debit and credit journal entries for a single account, optionally linked to a Q member using the database."""
    search_code: str  # Zoekcode (person ID)
    description: str  # Omschrijving (person name)
    debit: List[DavilexJournalEntry]
    credit: List[DavilexJournalEntry]

    @cached_property
    def q_person(self):
        try:
            return Person.objects.get(person_id=self.search_code)
        except Person.DoesNotExist:
            return None

    def get_email(self) -> str:
        if not self.q_person:
            return ''
        return self.q_person.email

    def get_iban(self) -> str:
        if not self.q_person:
            return ''
        return self.q_person.iban

    def get_open_debit(self) -> Decimal:
        return sum((d.open for d in self.debit), Decimal('0.00'))

    def get_open_credit(self) -> Decimal:
        return sum((d.open for d in self.credit), Decimal('0.00'))

    def get_total_open(self) -> Decimal:
        return self.get_open_debit() - self.get_open_credit()


def parse_davilex_report(data: str) -> List[DavilexBook]:
    """Parses Davilex data which was exported using 'Rapportage kopieren naar Excel'.

    Args:
        data: The data that was copied from Davilex (as string).
    """
    res = []
    with StringIO(data) as f:
        next(f)  # Skip the first header line

        while True:
            # Get first non-empty line, has person ID (zoekcode)
            try:
                while True:
                    line = next(f)  # type: str
                    if line.strip():
                        break  # Line is non-empty
            except StopIteration:
                break  # End of file reached
            fields = line.split('\t')
            search_code = fields[1]  # Person ID/zoekcode
            description = fields[2]  # Account description
            if not search_code or not description:
                # Search code and description must exist
                raise ValueError("Invalid report format.")

            # Parse journal entries on next lines (boekstukken)
            entries = []
            while True:
                fields = next(f).split('\t')
                if not fields[0]:
                    # Reached end of entries
                    break
                entries.append(DavilexJournalEntry.from_line(fields))

            # Sanity check: compare total amounts
            amount_total = parse_amount(fields[6])
            paid_total = parse_amount(fields[7])
            open_total = parse_amount(fields[8])

            amount_sum = sum(e.amount for e in entries)
            paid_sum = sum(e.paid for e in entries)
            open_sum = sum(e.open for e in entries)
            if amount_total != amount_sum or paid_total != paid_sum or open_total != open_sum:
                raise ValueError("Amounts don't sum up to expected totals.")

            # Done
            res.append(DavilexBook(search_code, description, entries))

    logger.debug("Parsed Davilex report: %s", res)
    return res


def combine_reports(debit: List[DavilexBook], credit: List[DavilexBook]) -> List[DavilexAccount]:
    """Combine separate debit and credit reports on the search code (person ID)."""
    accounts = {}

    # Create account for each debit book
    for book in debit:
        # Sanity check for duplicate search codes
        if book.search_code in accounts:
            raise ValueError("Duplicate search code in debit.")
        accounts[book.search_code] = DavilexAccount(book.search_code, book.description, debit=book.entries, credit=[])

    # Add the credit books to the accounts
    for book in credit:
        if book.search_code in accounts:
            # Sanity checks for duplicate credit entries and description
            if accounts[book.search_code].credit:
                raise ValueError("Duplicate search code in credit.")
            if accounts[book.search_code].description != book.description:
                raise ValueError("Credit/debit book descriptions not equal.")
            accounts[book.search_code].credit = book.entries
        else:
            accounts[book.search_code] = DavilexAccount(
                book.search_code,
                book.description,
                debit=[],
                credit=book.entries
            )
    return list(accounts.values())
