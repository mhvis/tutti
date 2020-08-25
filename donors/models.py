from django.db import models

from django_countries.fields import CountryField
from localflavor.generic.models import IBANField


class Donor(models.Model):
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField("email address", blank=True)
    salutation = models.CharField(max_length=30,
                                  choices=(('heer', 'Heer'), ('mevrouw', 'Mevrouw')),
                                  blank=True,
                                  help_text="Aanhef, om eventueel te gebruiken bij automatische e-mails.")

    # Address
    street = models.CharField(max_length=150, blank=True)
    postal_code = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=150, blank=True)
    country = CountryField(blank=True, default='NL')

    iban = IBANField(blank=True, verbose_name='IBAN')

    amount = models.DecimalField(max_digits=8,
                                 decimal_places=2,
                                 null=True,
                                 blank=True,
                                 help_text="Yearly donation amount.")

    newsletter = models.BooleanField(null=True,
                                     help_text="Whether the donor wants to receive the newsletter.")

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name).strip()
