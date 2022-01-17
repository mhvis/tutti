import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.forms import Textarea

from members.models import QGroup
from pennotools.core.davilex import combine_reports, parse_davilex_report


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


class ContributionExemptionForm(forms.Form):
    group = forms.ModelChoiceField(queryset=QGroup.objects.all().order_by('name'))
    student = forms.DecimalField(decimal_places=2,
                                 min_value=0)
    non_student = forms.DecimalField(decimal_places=2,
                                     min_value=0,
                                     label="Burger")


class BaseContributionExemptionFormSet(forms.BaseFormSet):
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


ContributionExemptionFormSet = forms.formset_factory(ContributionExemptionForm,
                                                     formset=BaseContributionExemptionFormSet,
                                                     extra=0)


def qrekening_initial_description():
    return 'Qrekening {}'.format(datetime.date.today().strftime('%B %Y'))


class QRekeningForm(forms.Form):
    """Form which parses the Davilex report during cleaning.

    It shows a validation error when parsing fails.
    """
    debit = forms.CharField(widget=Textarea,
                            strip=False,
                            help_text="Debit report exported from Davilex using 'Rapport kopiëren'.")
    credit = forms.CharField(widget=Textarea, strip=False, help_text="Davilex credit report.")
    description = forms.CharField(help_text="Description shown on the debtor direct debit statement.",
                                  max_length=35,
                                  initial=qrekening_initial_description)

    @staticmethod
    def _parse_davilex(data):
        # Converts ValueError to ValidationError
        try:
            return parse_davilex_report(data)
        except ValueError as e:
            raise ValidationError(f"Could not parse report, error: \"{e}\". See code for details.")

    def clean_debit(self):
        return self._parse_davilex(self.cleaned_data['debit'])

    def clean_credit(self):
        return self._parse_davilex(self.cleaned_data['credit'])

    def clean(self):
        # This method combines debit and credit on person ID
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit')
        credit = cleaned_data.get('credit')
        # 'is not None' is maybe necessary in case a value is [] (empty list)
        if debit is not None and credit is not None:
            try:
                cleaned_data['accounts'] = combine_reports(debit, credit)
            except ValueError as e:
                raise ValidationError(f"Could not parse report, error: \"{e}\". See code for details.")
        return cleaned_data

    # kenmerk = forms.CharField(max_length=35,
    #                           label="Kenmerk",
    #                           help_text="Het kenmerk van de machtiging die door de debiteur ondertekend is. "
    #                                     "Dit kenmerk moet uniek zijn per adres. "
    #                                     "Het staat ook bekend als mandaat-ID of mandaatkenmerk.")
