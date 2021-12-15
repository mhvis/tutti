from io import BytesIO

import xlrd
import xlsxwriter
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView

from pennotools.contributie.process import write_contributie, write_contributie_sepa, ContributionException
from pennotools.forms import ContributionForm, ContributionExceptionFormSet, QrekeningForm
from pennotools.qrekening.process import combine_persons
from pennotools.qrekening.wb import write_qrekening, read_exc, write_sepa


class TreasurerAccessMixin(PermissionRequiredMixin):
    """Use this mixin to protect views from prying eyes."""
    permission_required = 'pennotools.can_access'


class QRekeningView(TreasurerAccessMixin, TemplateView):
    template_name = 'pennotools/qrekening.html'

    def get(self, request, *args, **kwargs):
        context = {
            "form": QrekeningForm(),
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """Process a Q-rekening debtor or creditor file and download Qrekening."""
        if 'Debit' not in request.FILES or 'Credit' not in request.FILES:
            return self.get(request, form_invalid=True)

        form = QrekeningForm(request.POST)

        debit = request.FILES['Debit']
        credit = request.FILES['Credit']

        try:
            wb_debit = xlrd.open_workbook(file_contents=debit.read())
            wb_credit = xlrd.open_workbook(file_contents=credit.read())
        except xlrd.XLRDError as e:
            return self.get(request, file_invalid=e)

        # Write Excel workbook into memory
        output = BytesIO()
        wb = xlsxwriter.Workbook(output)

        # Process workbook
        try:
            dav_persons = read_exc(wb_debit, True, read_exc(wb_credit, False, {}))
        except ValueError as e:
            return self.get(request, file_invalid=e)
        combine_persons(dav_persons)
        if 'qrekening' in request.POST:
            write_qrekening(dav_persons, wb)
        elif 'sepa' in request.POST:
            write_sepa(dav_persons, wb, kenmerk=form.data['kenmerk'])

        # Write workbook
        wb.close()
        output.seek(0)
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s.xlsx' % (
            'SEPA' if 'sepa' in request.POST else ('qrekening' if 'qrekening' in request.POST else 'UNKNOWN')
        )
        return response


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
                exceptions.append(ContributionException(group=form_data["group"],
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
