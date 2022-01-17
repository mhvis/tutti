import csv

import xlsxwriter
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView, FormView

from pennotools.core.contribution import ContributionExemption, get_contributie, contributie_header, \
    contribution_sepa_amounts
from pennotools.core.qrekening import qrekening_sepa_amounts, get_qrekening, qrekening_header
from pennotools.core.rabo import rabo_sepa
from pennotools.core.workbook import write_sheet
from pennotools.forms import ContributionForm, ContributionExemptionFormSet, QRekeningForm


class TreasurerAccessMixin(PermissionRequiredMixin):
    """Use this mixin to protect views from prying eyes."""
    permission_required = 'pennotools.can_access'


class QRekeningView(TreasurerAccessMixin, FormView):
    template_name = 'pennotools/qrekening.html'

    form_class = QRekeningForm

    def form_valid(self, form):
        # Davilex parsing happens during form cleaning
        accounts = form.cleaned_data['accounts']

        if 'sepa' in self.request.POST:
            # Get the amounts for SEPA
            debits = qrekening_sepa_amounts(accounts)

            # Create and write the Rabobank CSV
            table = rabo_sepa(debits, form.cleaned_data['description'])

            response = HttpResponse(
                content_type='text/csv',
                headers={'Content-Disposition': 'attachment; filename="rabo_sepa.csv"'},
            )
            writer = csv.writer(response)
            writer.writerows(table)
            return response

        else:
            # Get Qrekening sheets
            creditors, debtors, debtors_self, external = get_qrekening(accounts)
            # Write Excel workbook in response
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': 'attachment; filename="qrekening.xlsx"'},
            )
            workbook = xlsxwriter.Workbook(response)
            write_sheet(workbook, 'Crediteuren', qrekening_header, creditors)
            write_sheet(workbook, 'Debiteuren', qrekening_header, debtors)
            write_sheet(workbook, 'DebiteurenZelf', qrekening_header, debtors_self)
            write_sheet(workbook, 'Externen', qrekening_header, external)
            workbook.close()
            return response


class ContributionView(TreasurerAccessMixin, TemplateView):
    template_name = "pennotools/contribution.html"

    def get(self, request, *args, **kwargs):
        context = {
            "form": ContributionForm(),
            "exceptions_formset": ContributionExemptionFormSet(),
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = ContributionForm(request.POST)
        exceptions_formset = ContributionExemptionFormSet(request.POST)
        if form.is_valid() and exceptions_formset.is_valid():
            # Collect exemptions
            exemptions = []
            for form_data in exceptions_formset.cleaned_data:
                # Loop over the data of all exception forms
                if not form_data.get("group"):
                    # There may be empty forms which should be ignored
                    continue
                exemptions.append(ContributionExemption(group=form_data["group"],
                                                        student=form_data["student"],
                                                        non_student=form_data["non_student"]))

            if 'contribution_file' in request.POST:
                # Get contribution sheets
                debtors, debtors_self = get_contributie(form.cleaned_data['student'],
                                                        form.cleaned_data['non_student'],
                                                        form.cleaned_data['administration_fee'], exemptions)

                # Write to response
                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': 'attachment; filename="contributielijst.xlsx"'},
                )
                workbook = xlsxwriter.Workbook(response)
                write_sheet(workbook, 'Debiteuren', contributie_header, debtors)
                write_sheet(workbook, 'DebiteurenZelf', contributie_header, debtors_self)
                workbook.close()
                return response
            else:
                amounts = contribution_sepa_amounts(form.cleaned_data['student'],
                                                    form.cleaned_data['non_student'],
                                                    exemptions)
                table = rabo_sepa(amounts, form.cleaned_data['description'])

                # Write CSV
                response = HttpResponse(
                    content_type='text/csv',
                    headers={'Content-Disposition': 'attachment; filename="rabo_sepa.csv"'},
                )
                writer = csv.writer(response)
                writer.writerows(table)
                return response
            # Unreachable
        # One of the forms was not valid, render again
        context = {
            "form": form,
            "exceptions_formset": exceptions_formset,
        }
        return self.render_to_response(context)
