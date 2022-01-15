import csv

import xlsxwriter
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.mail import mail_admins
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic import TemplateView, FormView

from pennotools.core.contribution import write_contributie_sepa, ContributionExemption, \
    get_contributie, contributie_header
from pennotools.core.davilex import parse_davilex_report, combine_reports
from pennotools.core.qrekening import qrekening_sepa_amounts, get_qrekening, qrekening_header
from pennotools.core.rabo import rabo_sepa
from pennotools.core.wb import write_sheet
from pennotools.forms import ContributionForm, ContributionExceptionFormSet, QRekeningForm


class TreasurerAccessMixin(PermissionRequiredMixin):
    """Use this mixin to protect views from prying eyes."""
    permission_required = 'pennotools.can_access'


class QRekeningView(TreasurerAccessMixin, FormView):
    template_name = 'pennotools/qrekening.html'

    form_class = QRekeningForm

    def form_valid(self, form):
        # Temporary, for testing/auditing purposes, log form data by mail
        mail_admins("Q-rekening log", f"Form data:\n{form.cleaned_data}\n\nPOST data:\n{self.request.POST}")

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
                return response
            else:
                write_contributie_sepa(wb,
                                       form.cleaned_data["student"],
                                       form.cleaned_data["non_student"],
                                       exemptions, kenmerk=form.data['kenmerk'])

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
