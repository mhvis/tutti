from datetime import datetime

"""
- A davilex transaction
"""
class Boekstuk:
    """
    - Input: | p: DavilexPerson
             | amount: int
             | description: string (dd/mm/yyyy)
    """
    def __init__(self, p, amount, date, description):
        self.relation = p
        self.amount = amount
        self.date = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(date) - 2)
        self.description = description

    def get_date(self):
        return self.date.strftime("%d-%m-%Y")

class DavilexPerson:
    def __init__(self, p):
        self.name = p['Omschrijving']
        self.id = p['Zoekcode']
        # Sets of Boekstuk objects
        self.debet = []
        self.credit = []
        self.qPerson = None

    """
    - addBoekstuk: Create a Boekstuk object from a dictionary
    - Input: | row: list of tuples (dictionary)
             | debet: boolean whether it is debet (true) or credit (false)
    """
    def addBoekstuk(self, row, debet):
        b = Boekstuk(self, row['Openstaand'], row['Fac/Bet Datum'], row['Omschrijving'])
        if (debet):
            self.debet.append(b)
        else:
            self.credit.append(b)

    """
    - addPerson: Add an LDAP person to the object
    - Input: | p: Person
    """
    def addPerson(self, p):
        if (self.qPerson == None):
            if (p.person_id == self.id):
                self.qPerson = p
        else: 
            raise Exception('Duplicate qID in the database')

    def get_email(self):
        if (self.qPerson == None):
            return 'None'
        return self.qPerson.email

    def get_iban(self):
        if (self.qPerson == None):
            return ''
        return self.qPerson.iban

    def get_total(self):
        total = 0
        for d in self.debet:
            total += d.amount
        for c in self.credit:
            total -= c.amount
        return total

    def get_debet_amounts(self):
        return '\n'.join([str(d.amount) for d in self.debet])

    def get_credit_amounts(self):
        return '\n'.join([str(c.amount) for c in self.credit])

    def get_debet_dates(self):
        return '\n'.join([d.get_date() for d in self.debet])

    def get_credit_dates(self):
        return '\n'.join([c.get_date() for c in self.credit])

    def get_debet_total(self):
        return '{0:.2f}'.format(sum(d.amount for d in self.debet))

    def get_credit_total(self):
        return '{0:.2f}'.format(sum(c.amount for c in self.credit))

    def get_debet_description(self):
        return '\n'.join([d.description for d in self.debet])

    def get_credit_description(self):
        return '\n'.join([c.description for c in self.credit])



