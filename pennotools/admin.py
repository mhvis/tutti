from django.contrib import admin
from .models import Qrekening, DavilexData
from .src.qrekening.process import read_exc, combinePersons, initializeWorkbook, writeSepa

# Register your models here.
class DavilexDataInline(admin.TabularInline):
    model = DavilexData
    max_num = 2


@admin.register(Qrekening)
class QrekeningAdmin(admin.ModelAdmin):
    readonly_fields = ('date', 'qrekening')
    inlines = [DavilexDataInline]
    list_display = ('date', 'due')
    ordering = ('date', 'due')

    def save_model(self, request, obj, form, change):
        super(QrekeningAdmin, self).save_model(request, obj, form, change)
        # Attempt to generate Q rekening file
        files = DavilexData.objects.filter(qrekening=self)
        for file in files:
            if file.type == 'creditor':
                creditors = file
            else:
                debtors = file
        dav_persons = read_exc(debtors, True, read_exc(creditors, False, {}))
        combinePersons(dav_persons)
        initializeWorkbook(dav_persons)
        writeSepa(dav_persons)




@admin.register(DavilexData)
class DavilexDataAdmin(admin.ModelAdmin):
    pass
