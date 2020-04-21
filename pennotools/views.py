from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from .forms import UploadFileForm
import xlrd
import xlsxwriter
from io import BytesIO


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
        ws = wb.add_worksheet('TestSheet')
        ws.write(0, 0, 'Test Value')

        # Write workbook
        wb.close()
        output.seek(0)
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s_Report.xlsx' % 'wessel'
        return response
    else:
        form = UploadFileForm()
    return render(request, 'pennotools/qrekening.html', {'form': form})