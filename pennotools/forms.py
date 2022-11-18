import datetime
from contextlib import contextmanager
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.forms import Textarea
from django.utils.safestring import mark_safe

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
    sepa_split = forms.DecimalField(min_value=Decimal('0.01'), decimal_places=2, label="SEPA split",
                                    help_text="SEPA debit rows with a value larger than this amount will be "
                                              "split over multiple rows.",
                                    initial=Decimal('130.00'))


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


@contextmanager
def to_validation_error():
    """Context manager that reraises errors from parsing as ValidationError."""
    try:
        yield
    except (ValueError, IndexError) as e:
        raise ValidationError(mark_safe(
            f"Could not parse report. See code or <a href='mailto:sysop@esmgquadrivium.nl'>ask</a> for details."
            f" The error encountered was: '{e}'."))


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
    sepa_split = forms.DecimalField(min_value=Decimal('0.01'), decimal_places=2, label="SEPA split",
                                    help_text="SEPA debit rows with a value larger than this amount will be "
                                              "split over multiple rows.",
                                    initial=Decimal('130.00'))

    def clean_debit(self):
        with to_validation_error():
            return parse_davilex_report(self.cleaned_data['debit'])

    def clean_credit(self):
        with to_validation_error():
            return parse_davilex_report(self.cleaned_data['credit'])

    def clean(self):
        # This method combines debit and credit on person ID
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit')
        credit = cleaned_data.get('credit')
        # 'is not None' is maybe necessary in case the value is an empty list
        if debit is not None and credit is not None:
            with to_validation_error():
                cleaned_data['accounts'] = combine_reports(debit, credit)
        return cleaned_data

class XmlMakerForm(forms.Form):
    SEPA_csv_file = forms.CharField(widget=Textarea,
                            strip=False,
                            help_text="Open het SEPA csv file in Notepad and paste it in here")