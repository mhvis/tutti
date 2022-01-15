import datetime

from django import forms
from django.forms import Textarea

from members.models import QGroup


def sepa_initial_description():
    return 'Contribution {}'.format(datetime.date.today().strftime('%Y'))


class ContributionForm(forms.Form):
    student = forms.DecimalField(decimal_places=2,
                                 min_value=0,
                                 help_text="Hoogte van de contributie voor studenten.")
    non_student = forms.DecimalField(decimal_places=2,
                                     min_value=0,
                                     label="Burger",
                                     help_text="Hoogte van de contributie voor burgers.")
    administration_fee = forms.DecimalField(decimal_places=2,
                                            min_value=0,
                                            initial=6,
                                            label="Administratiekosten",
                                            help_text="Wordt alleen toegepast bij personen zonder SEPA machtiging.")
    description = forms.CharField(help_text="Omschrijving voor de SEPA incasso.",
                                  max_length=35,
                                  initial=sepa_initial_description,
                                  label="Omschrijving")


class ContributionExceptionForm(forms.Form):
    group = forms.ModelChoiceField(queryset=QGroup.objects.all().order_by('name'))
    student = forms.DecimalField(decimal_places=2,
                                 min_value=0)
    non_student = forms.DecimalField(decimal_places=2,
                                     min_value=0,
                                     label="Burger")


class BaseContributionExceptionFormSet(forms.BaseFormSet):
    def clean(self):
        """Checks that the groups are unique."""
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        groups = []
        for form in self.forms:
            group = form.cleaned_data.get("group")
            if not group:
                continue  # Form might be empty
            if group in groups:
                raise forms.ValidationError("Groups need to be distinct.")
            groups.append(group)


ContributionExceptionFormSet = forms.formset_factory(ContributionExceptionForm,
                                                     formset=BaseContributionExceptionFormSet,
                                                     extra=0)


def qrekening_initial_description():
    return 'Qrekening {}'.format(datetime.date.today().strftime('%B %Y'))


class QRekeningForm(forms.Form):
    debit = forms.CharField(widget=Textarea,
                            strip=False,
                            help_text="Debit report exported from Davilex using 'Rapport kopiëren'.")
    credit = forms.CharField(widget=Textarea, strip=False, help_text="Davilex credit report.")
    description = forms.CharField(help_text="Description shown on the debtor direct debit statement.",
                                  max_length=35,
                                  initial=qrekening_initial_description)
    # kenmerk = forms.CharField(max_length=35,
    #                           label="Kenmerk",
    #                           help_text="Het kenmerk van de machtiging die door de debiteur ondertekend is. "
    #                                     "Dit kenmerk moet uniek zijn per adres. "
    #                                     "Het staat ook bekend als mandaat-ID of mandaatkenmerk.")
