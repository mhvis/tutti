from datetime import datetime


class Boekstuk:
    """A Davilex transaction.

    - Input: | person: DavilexPerson
             | description: string (dd/mm/yyyy)
    """

    def __init__(self, amount: float, date: datetime, description: str):
        self.amount = amount
        self.date = date
        self.description = description

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Boekstuk):
            return False
        if self.amount != o.amount or self.date != o.date or self.description != o.description:
            return False
        return True

    def get_date(self):
        return self.date.strftime("%d-%m-%Y")


class DavilexPerson:
    def __init__(self, name: str, id: str):
        self.name = name
        self.id = id
        # Lists of Boekstuk objects
        self.debet = []
        self.credit = []
        self.q_person = None

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, DavilexPerson):
            return False
        if self.name != o.name or self.id != o.id or self.debet != o.debet or self.credit != o.credit:
            return False
        return True

    def add_boekstuk(self, debet: bool, amount: float, date: datetime, description: str):
        """Create a Boekstuk object from a dictionary."""
        b = Boekstuk(amount, date, description)
        if debet:
            self.debet.append(b)
        else:
            self.credit.append(b)

    def add_person(self, p):
        """Link a database person with this object.

        Args:
            p: Person.
        """
        if self.q_person:
            raise ValueError("DavilexPerson is linked")
        if p.person_id != self.id:
            raise ValueError("Person ID inconsistent")
        self.q_person = p

    def get_email(self):
        """Returns empty string if e-mail is unknown."""
        if self.q_person is None:
            return ''
        return self.q_person.email

    def get_iban(self):
        if self.q_person is None:
            return ''
        return self.q_person.iban

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
