import csv
from io import BytesIO

import xlsxwriter
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic import TemplateView, FormView

from pennotools.contributie.process import write_contributie, write_contributie_sepa, ContributionExemption
from pennotools.forms import ContributionForm, ContributionExceptionFormSet, QRekeningForm
from pennotools.qrekening.davilex import parse_davilex_report, combine_reports
from pennotools.qrekening.process import qrekening_sepa_amounts, get_qrekening, qrekening_header
from pennotools.qrekening.rabo import rabo_sepa
from pennotools.qrekening.wb import write_sheet


class TreasurerAccessMixin(PermissionRequiredMixin):
    """Use this mixin to protect views from prying eyes."""
    permission_required = 'pennotools.can_access'


class QRekeningView(TreasurerAccessMixin, FormView):
    template_name = 'pennotools/qrekening.html'

    form_class = QRekeningForm

    def form_valid(self, form):
        # Parse input
        debit = parse_davilex_report(form.cleaned_data['debit'])
        credit = parse_davilex_report(form.cleaned_data['credit'])
        # Combine on person ID
        accounts = combine_reports(debit, credit)

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

        elif 'qrekening' in self.request.POST:
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
        return HttpResponseBadRequest()


class ContributionView(TreasurerAccessMixin, TemplateView):
    template_name = "pennotools/contribution.html"

    def get(self, request, *args, **kwargs):
        context = {
            "form": ContributionForm(),
            "exceptions_formset": ContributionExceptionFormSet(),
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = ContributionForm(request.POST)
        exceptions_formset = ContributionExceptionFormSet(request.POST)
        if form.is_valid() and exceptions_formset.is_valid():
            # Process form
            # Write Excel workbook into memory
            output = BytesIO()
            wb = xlsxwriter.Workbook(output)

            exceptions = []
            for form_data in exceptions_formset.cleaned_data:
                # Loop over the data of all exception forms
                if not form_data.get("group"):
                    # There may be empty forms which should be ignored
                    continue
                exceptions.append(ContributionExemption(group=form_data["group"],
                                                        student=form_data["student"],
                                                        non_student=form_data["non_student"]))

            if 'contribution_file' in request.POST:
                write_contributie(wb,
                                  form.cleaned_data["student"],
                                  form.cleaned_data["non_student"],
                                  form.cleaned_data["administration_fee"],
                                  exceptions)
            else:
                write_contributie_sepa(wb,
                                       form.cleaned_data["student"],
                                       form.cleaned_data["non_student"],
                                       exceptions, kenmerk=form.data['kenmerk'])

            # Write workbook
            wb.close()
            output.seek(0)
            response = HttpResponse(
                output,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename={}.xlsx'.format(
                'contributielijst' if 'contribution_file' in request.POST else 'sepa'
            )
            return response
        # One of the forms was not valid, render again
        context = {
            "form": form,
            "exceptions_formset": exceptions_formset,
        }
        return self.render_to_response(context)
