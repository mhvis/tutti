from django import forms

from members.models import QGroup


class ContributionForm(forms.Form):
    kenmerk = forms.CharField(max_length=35,
                              label="Kenmerk",
                              help_text="Het kenmerk van de machtiging die door de debiteur ondertekend is. "
                                        "Dit kenmerk moet uniek zijn per adres. "
                                        "Het staat ook bekend als mandaat-ID of mandaatkenmerk.")
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


class ContributionExceptionForm(forms.Form):
    group = forms.ModelChoiceField(queryset=QGroup.objects.all())
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


class QrekeningForm(forms.Form):
    kenmerk = forms.CharField(max_length=35,
                              label="Kenmerk",
                              help_text="Het kenmerk van de machtiging die door de debiteur ondertekend is. "
                                        "Dit kenmerk moet uniek zijn per adres. "
                                        "Het staat ook bekend als mandaat-ID of mandaatkenmerk.")

    Debit = forms.FileField()
    Credit = forms.FileField()
