from xlrd import open_workbook
import datetime
import xlwt
from .qPerson import DavilexPerson
from .config import sepa_headers
from qluis.models import Person


def read_exc(sheet, debet, persons):
    """
    - read_exc: reads an excel sheet
    - Input: | sheet: a string of the path to the excel sheet
             | debet: boolean whether it is debet (true) or credit (false)
             | persons: dict (qID:DavilexPerson)
    - Returns: list(DavilexPerson)
    """
    wb = open_workbook(sheet)
    for s in wb.sheets():
        col_names = s.row(0)
        person_finished = True
        for row in range(1, s.nrows):
            col_value = {}
            for name, col in zip(col_names, range(s.ncols)):
                value = (s.cell(row,col).value)
                col_value[name.value] = value
            if col_value['Zoekcode'] != '' and 'totaal' in col_value['Omschrijving']:
                person_finished = True
            elif not person_finished:
                current_person.addBoekstuk(col_value, debet)
            elif col_value['Zoekcode'] != '' and col_value['Omschrijving'] != '':
                try: 
                    current_person = persons[col_value['Zoekcode']]
                except: 
                    current_person = DavilexPerson(col_value)
                    persons[col_value['Zoekcode']] = current_person
                person_finished = False
    return persons


def combinePersons(davilexPeople):
    """
    - Link a Person to a DavilexPerson
    """
    for name,value in davilexPeople.items():
        try:
            person = Person.objects.get(person_id__exact=value.id)
            if person:
                value.addPerson(person)
        except Person.DoesNotExist:
            pass


def get_value(p, header):
    if header == 'StuurStatus': return ''
    if header == 'CODE' or header == 'mandaatid': return p.id
    if header == 'Naam' or header == 'naam': return p.name
    if header == 'Opmerkingen': return ''
    if header == 'Email': return p.get_email()
    if header == 'Bankreknr' or header == 'IBAN': return p.get_iban()
    if header == 'Deb Tot Open': return p.get_debet_total()
    if 'Deb Omschrijving' in header: return p.get_debet_description()
    if header == 'Deb Datum': return p.get_debet_dates()
    if header == 'Deb Bedrag': return p.get_debet_amounts()
    if header == 'Deb Open': return p.get_debet_amounts()
    if header == 'Cred Tot Open': return p.get_credit_total()
    if 'Cred Omschrijving' in header: return p.get_credit_description()
    if header == 'Cred Datum': return p.get_credit_dates()
    if header == 'Cred Bedrag': return p.get_credit_amounts()
    if header == 'Cred Open': return p.get_credit_amounts()
    if header == 'Totaal Open Tekst': return '{0:.2f}'.format(p.get_total())
    if header == 'Totaal Open Temp' or header == 'bedrag': return p.get_total()
    if header == 'beschrijving': return 'Qrekening Maart 2019'
    if header == 'endtoendid': return p.id+datetime.date.today().strftime('%m')+datetime.date.today().strftime('%y')
    return ''


"""
- Write people to the excelsheet
"""
def initializeWorkbook(davPeople, path):
    workbook = xlwt.Workbook()
    creditors =  workbook.add_sheet('Crediteuren')
    cred_row = 1
    debtors = workbook.add_sheet('Debiteuren')
    debt_row = 1
    debtorsSelf = workbook.add_sheet('DebiteurenZelf')
    debtSelf_row = 1
    external = workbook.add_sheet('Externen')
    external_row = 1
    headers = ['StuurStatus','CODE','Naam','Opmerkingen','Email','Bankreknr','Deb Tot Open','Deb Omschrijving','Deb Datum','Deb Bedrag','Deb Open','Cred Tot Open','Cred Omschrijving','Cred Datum','Cred Bedrag','Cred Open','Totaal Open Tekst','Totaal Open Temp']
    for s in [creditors,debtors,debtorsSelf,external]:
        for i in range(len(headers)):
            s.write(0,i,headers[i])
    for key,p in davPeople.items():
        #Is this person from Q?
        if (p.qPerson != None):
            if (p.get_total() < 0):
                for i in range(len(headers)):
                    creditors.write(cred_row,i,get_value(p,headers[i]))
                cred_row += 1
            elif (p.get_total() >= 0 and len(p.get_iban()) < 1):
                for i in range(len(headers)):
                    debtorsSelf.write(debtSelf_row,i,get_value(p,headers[i]))
                debtSelf_row += 1
            else:
                for i in range(len(headers)):
                    debtors.write(debt_row,i,get_value(p,headers[i]))
                debt_row += 1
        else:
            for i in range(len(headers)):
                external.write(external_row,i,get_value(p,headers[i]))
            external_row += 1
    name = 'Qrekening.xls'
    workbook.save(path + name)
    return path + name


def writeSepa(davPeople, path):
    workbook = xlwt.Workbook()
    debtors = workbook.add_sheet('Debiteuren')
    debt_row = 1
    for s in [debtors]:
        for i in range(len(sepa_headers)):
            s.write(0,i,sepa_headers[i])
    for key,p in davPeople.items():
        if (p.qPerson != None):
            if (p.get_total() < 0):
                pass;
            elif (p.get_total() >= 0 and len(p.get_iban()) < 1):
                pass;
            else:
                total = p.get_total()
                while (total > 100):
                    for i in range(len(sepa_headers)):
                        if sepa_headers[i] == 'bedrag':
                            debtors.write(debt_row,i,100)
                        else:
                            debtors.write(debt_row,i,get_value(p,sepa_headers[i]))
                    total -= 100
                    debt_row += 1
                for i in range(len(sepa_headers)):
                        if sepa_headers[i] == 'bedrag':
                            debtors.write(debt_row,i,total)
                        else:
                            debtors.write(debt_row,i,get_value(p,sepa_headers[i]))
                debt_row += 1
    name = 'QrekeningSEPA.xls'
    workbook.save(path + name)
    return path + name
