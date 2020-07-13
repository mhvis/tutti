from io import BytesIO

import xlrd
import xlsxwriter
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView

from pennotools.qrekening.process import combine_persons
from pennotools.qrekening.wb import write_qrekening, read_exc, write_sepa

from pennotools.contributie.process import write_contributie, write_contributie_sepa

from members.models import QGroup


class TreasurerAccessMixin(PermissionRequiredMixin):
    """Use this mixin to protect views from prying eyes."""
    permission_required = 'pennotools.can_access'


class QRekeningView(TreasurerAccessMixin, TemplateView):
    template_name = 'pennotools/qrekening.html'

    def post(self, request, *args, **kwargs):
        """Process a Q-rekening debtor or creditor file and download Qrekening."""
        if 'Debit' not in request.FILES or 'Credit' not in request.FILES:
            return self.get(request, form_invalid=True)

        debit = request.FILES['Debit']
        credit = request.FILES['Credit']

        wb_debit = xlrd.open_workbook(file_contents=debit.read())
        wb_credit = xlrd.open_workbook(file_contents=credit.read())

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


class ContributieView(TreasurerAccessMixin, TemplateView):
    template_name = 'pennotools/contributie.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = {}
        for group in QGroup.objects.all():
            context['groups'][group.id] = group.name
        return context

    def post(self, request, *args, **kwargs):
        """Process the contributie form and download the Contributie files."""
        filters = {}
        for value in range(len(QGroup.objects.all())):
            try:
                filters[request.POST['inputGroupSelect' + str(value)]] = request.POST['filter' + str(value)]
            except KeyError:
                break

        # Write Excel workbook into memory
        output = BytesIO()
        wb = xlsxwriter.Workbook(output)

        if 'contributie' in request.POST:
            write_contributie(wb, int(request.POST['Student']), int(request.POST['Administration']), filters)
        elif 'sepa' in request.POST:
            write_contributie_sepa(wb, int(request.POST['Student']), filters)

        # Write workbook
        wb.close()
        output.seek(0)
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s.xlsx' % (
            'SEPA' if 'sepa' in request.POST else ('Contributie' if 'contributie' in request.POST else 'UNKNOWN')
        )
        return response
