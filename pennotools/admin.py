from django.contrib import admin
from .models import Qrekening, DavilexData
from .src.qrekening.process import read_exc, combinePersons, initializeWorkbook, writeSepa
from django.conf import settings
import os


class DavilexDataInline(admin.TabularInline):
    model = DavilexData
    max_num = 2


def construct_qrekening(obj):
    files = DavilexData.objects.filter(qrekening=obj)
    path = settings.MEDIA_URL + 'qrekening/' + \
           str(obj.date.year).zfill(4) + '_' + \
           str(obj.date.month).zfill(2) + '_' + \
           str(obj.date.day).zfill(2) + '/'
    if not os.path.exists(path):
        os.makedirs(path)
    for file in files:
        if file.type == 'creditor':
            creditors = file.file.path
        else:
            debtors = file.file.path
    dav_persons = read_exc(debtors, True, read_exc(creditors, False, {}))
    combinePersons(dav_persons)
    qrekening = initializeWorkbook(dav_persons, path)
    sepa = writeSepa(dav_persons, path)
    obj.qrekening.name = qrekening
    obj.save()


@admin.register(Qrekening)
class QrekeningAdmin(admin.ModelAdmin):
    readonly_fields = ('date', 'qrekening')
    inlines = [DavilexDataInline]
    list_display = ('date', 'due')
    ordering = ('date', 'due')

    def response_add(self, request, obj, post_url_continue=None):
        construct_qrekening(obj)
        return super(QrekeningAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        construct_qrekening(obj)
        return super(QrekeningAdmin, self).response_change(request, obj)


@admin.register(DavilexData)
class DavilexDataAdmin(admin.ModelAdmin):
    pass
