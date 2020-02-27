from django.contrib import admin
from .models import Qrekening, DavilexData

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




@admin.register(DavilexData)
class DavilexDataAdmin(admin.ModelAdmin):
    pass
