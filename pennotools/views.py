from io import BytesIO

import xlrd
import xlsxwriter
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic import TemplateView

from pennotools.src.qrekening.process import read_exc, combine_persons, initialize_workbook, write_sepa


class TreasurerAccessMixin(PermissionRequiredMixin):
    """Use this mixin to protect views from prying eyes."""
    permission_required = 'pennotools.can_access'


class QRekeningView(TreasurerAccessMixin, TemplateView):
    template_name = 'pennotools/qrekening.html'

    def post(self, request, *args, **kwargs):
        """Process a Q-rekening debtor or creditor file and download Qrekening."""
        if 'Debit' not in request.FILES or 'Credit' not in request.FILES:
            return HttpResponseBadRequest('Need to provide debit and credit files')

        debit = request.FILES['Debit']
        credit = request.FILES['Credit']
        wb_debit = xlrd.open_workbook(file_contents=debit.read())
        wb_credit = xlrd.open_workbook(file_contents=credit.read())

        # Write Excel workbook into memory
        output = BytesIO()
        wb = xlsxwriter.Workbook(output)

        # Process workbook
        dav_persons = read_exc(wb_debit, True, read_exc(wb_credit, False, {}))
        combine_persons(dav_persons)
        if 'qrekening' in request.POST:
            initialize_workbook(dav_persons, wb)
        elif 'sepa' in request.POST:
            write_sepa(dav_persons, wb)

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
