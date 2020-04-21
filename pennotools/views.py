from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.shortcuts import render
import xlrd
import xlsxwriter
from io import BytesIO
from .src.qrekening.process import read_exc, combinePersons, initializeWorkbook, writeSepa


class QrekeningView(LoginRequiredMixin, TemplateView):
    template_name = 'pennotools/qrekening.html'


def get_debtor_creditor(request):
    """Process a Q-rekening debtor or creditor file and download Qrekening"""
    if request.method == 'POST':
        debit = request.FILES['Debit']
        credit = request.FILES['Credit']
        wb_debit = xlrd.open_workbook(file_contents=debit.read())
        wb_credit = xlrd.open_workbook(file_contents=credit.read())

        # Write Excel workbook into memory
        output = BytesIO()
        wb = xlsxwriter.Workbook(output)

        # Process workbook
        dav_persons = read_exc(wb_debit, True, read_exc(wb_credit, False, {}))
        combinePersons(dav_persons)
        initializeWorkbook(dav_persons, wb)

        # Write workbook
        wb.close()
        output.seek(0)
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=qrekening.xlsx'
        return response
    return render(request, 'pennotools/qrekening.html')