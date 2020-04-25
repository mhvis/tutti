import datetime
from pennotools.src.qrekening.qPerson import DavilexPerson
from pennotools.src.qrekening.config import sepa_headers, output_headers
from members.models import Person


def read_exc(wb, debet, persons):
    """Read the given excel sheet.

    - read_exc: reads an excel sheet
    - Input: | sheet: a string of the path to the excel sheet
             | debet: boolean whether it is debet (true) or credit (false)
             | persons: dict (qID:DavilexPerson)
    - Returns: list(DavilexPerson)
    """
    current_person = None
    for s in wb.sheets():
        col_names = s.row(0)
        person_finished = True
        for row in range(1, s.nrows):
            col_value = {}
            for name, col in zip(col_names, range(s.ncols)):
                value = s.cell(row, col).value
                col_value[name.value] = value
            if col_value['Zoekcode'] != '' and 'totaal' in col_value['Omschrijving']:
                person_finished = True
            elif not person_finished and current_person is not None:
                current_person.add_boekstuk(col_value, debet)
            elif col_value['Zoekcode'] != '' and col_value['Omschrijving'] != '':
                try:
                    current_person = persons[col_value['Zoekcode']]
                except KeyError:
                    current_person = DavilexPerson(col_value)
                    persons[col_value['Zoekcode']] = current_person
                person_finished = False
    return persons


def combine_persons(davilex_people):
    """Link a Person to a DavilexPerson."""
    for name, value in davilex_people.items():
        try:
            person = Person.objects.get(person_id__exact=value.id)
            if person:
                value.add_person(person)
        except Person.DoesNotExist:
            pass


def get_value(p, header):
    values = {
        'StuurStatus': '',
        'Opmerkingen': '',
        'CODE': p.id,
        'mandaatid': p.id,
        'Naam': p.name,
        'naam': p.name,
        'Email': p.get_email(),
        'Bankreknr': p.get_iban(),
        'IBAN': p.get_iban(),
        'Deb Tot Open': p.get_debet_total(),
        'Deb Datum': p.get_debet_dates(),
        'Deb Bedrag': p.get_debet_amounts(),
        'Deb Open': p.get_debet_amounts(),
        'Cred Tot Open': p.get_credit_total(),
        'Cred Datum': p.get_credit_dates(),
        'Cred Bedrag': p.get_credit_amounts(),
        'Cred Open': p.get_credit_amounts(),
        'Totaal Open Tekst': '{0:.2f}'.format(p.get_total()),
        'Totaal Open Temp': p.get_total(),
        'bedrag': p.get_total(),
        'beschrijving': 'Qrekening %s %s' % (datetime.datetime.today().strftime('%B'),
                                             datetime.datetime.today().strftime('%Y')),
        'endtoendid': p.id + datetime.date.today().strftime('%m') + datetime.date.today().strftime('%y')
    }
    if 'Deb Omschrijving' in header:
        return p.get_debet_description()
    elif 'Cred Omschrijving' in header:
        return p.get_credit_description()
    try:
        return values[header]
    except KeyError:
        return ''


def initialize_workbook(dav_people, workbook):
    """Initialize workbook to write people to the excelsheet."""
    creditors = workbook.add_worksheet('Crediteuren')
    debtors = workbook.add_worksheet('Debiteuren')
    debtors_self = workbook.add_worksheet('DebiteurenZelf')
    external = workbook.add_worksheet('Externen')
    for s in [creditors, debtors, debtors_self, external]:
        for i in range(len(output_headers)):
            s.write(0, i, output_headers[i])
    write_workbook(dav_people, creditors, debtors, debtors_self, external)
    return workbook


def write_row(ws, row, headers, p):
    for i in range(len(headers)):
        ws.write(row, i, get_value(p, headers[i]))
    return 1


def write_workbook(dav_people, creditors, debtors, debtors_self, external):
    """Write people to the excelsheet."""
    cred_row, debt_row, debt_self_row, external_row = (1, 1, 1, 1)
    for key, p in dav_people.items():
        # Is this person from Q?
        if p.qPerson is not None:
            if p.get_total() < 0:
                cred_row += write_row(creditors, cred_row, output_headers, p)
            elif p.get_total() >= 0 and len(p.get_iban()) < 1:
                debt_self_row += write_row(debtors_self, debt_self_row, output_headers, p)
            else:
                debt_row += write_row(debtors, debt_row, output_headers, p)
        else:
            external_row += write_row(external, external_row, output_headers, p)


def write_sepa_bedrag(ws, row, value, headers, p):
    for i in range(len(headers)):
        if headers[i] == 'bedrag':
            ws.write(row, i, value)
        else:
            ws.write(row, i, get_value(p, headers[i]))


def write_sepa(dav_people, workbook):
    debtors = workbook.add_worksheet('Debiteuren')
    debt_row = 1
    for s in [debtors]:
        for i in range(len(sepa_headers)):
            s.write(0, i, sepa_headers[i])
    for key, p in dav_people.items():
        if p.qPerson is not None:
            if p.get_total() < 0 or (p.get_total() >= 0 and len(p.get_iban()) < 1):
                pass
            else:
                total = p.get_total()
                while total > 100:
                    write_sepa_bedrag(debtors, debt_row, 100, sepa_headers, p)
                    total -= 100
                    debt_row += 1
                write_sepa_bedrag(debtors, debt_row, total, sepa_headers, p)
                debt_row += 1
    return workbook
