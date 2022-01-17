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
            raise ValueError("invalid amount format")
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
            raise ValueError("invalid boekstuk line format")
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
            # Get first book/account line, should have person ID/zoekcode
            try:
                # This generator skips empty lines
                fields = next(line for line in f if line.strip()).split('\t')
            except StopIteration:
                break  # End of file reached

            if not fields[1] and fields[2] == 'TOTAAL':
                # Line has 'TOTAAL', end reached
                #
                # Sanity check: very unnecessary, but let's make sure that the end total is correct,
                #   to ensure that no accounts/books have been missed or tampered with.
                expect_amount = parse_amount(fields[6])
                expect_paid = parse_amount(fields[7])
                expect_open = parse_amount(fields[8])
                # Had to Google the correct way for this: https://stackoverflow.com/a/36734643/2373688
                actual_amount = sum(y.amount for x in res for y in x.entries)
                actual_paid = sum(y.paid for x in res for y in x.entries)
                actual_open = sum(y.open for x in res for y in x.entries)
                if expect_amount != actual_amount or expect_paid != actual_paid or expect_open != actual_open:
                    raise ValueError("end total is incorrect")
                continue  # (continue instead of break in case there's additional data below this line)

            search_code = fields[1]  # Person ID/zoekcode
            description = fields[2]  # Account description
            if not search_code or not description:
                raise ValueError("invalid report format")

            # Parse journal entries on next lines (boekstukken)
            entries = []
            while True:
                fields = next(f).split('\t')
                if not fields[0]:
                    # Reached end of entries
                    break
                entries.append(DavilexJournalEntry.from_line(fields))

            # Sanity check: compare total amounts
            expect_amount = parse_amount(fields[6])
            expect_paid = parse_amount(fields[7])
            expect_open = parse_amount(fields[8])
            actual_amount = sum(e.amount for e in entries)
            actual_paid = sum(e.paid for e in entries)
            actual_open = sum(e.open for e in entries)
            if expect_amount != actual_amount or expect_paid != actual_paid or expect_open != actual_open:
                raise ValueError(f"book total is incorrect for {search_code}")

            # Store
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
            raise ValueError(f"duplicate search code '{book.search_code}' in debit")
        accounts[book.search_code] = DavilexAccount(book.search_code, book.description, debit=book.entries, credit=[])

    # Add the credit books to the accounts
    for book in credit:
        if book.search_code in accounts:
            # Sanity checks for duplicate credit entries and description
            if accounts[book.search_code].credit:
                raise ValueError(f"duplicate search code '{book.search_code}' in credit")
            if accounts[book.search_code].description != book.description:
                raise ValueError(f"credit/debit book descriptions not equal for '{book.search_code}'")
            accounts[book.search_code].credit = book.entries
        else:
            accounts[book.search_code] = DavilexAccount(
                book.search_code,
                book.description,
                debit=[],
                credit=book.entries
            )
    return list(accounts.values())
