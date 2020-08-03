"""Sets up Django Q (job scheduler) models in the admin site."""
from django.contrib import admin
from django_q.admin import ScheduleAdmin, TaskAdmin, FailAdmin, QueueAdmin
from django_q.models import Schedule, Success, Failure, OrmQ


class NoPermissionsMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class MyScheduleAdmin(NoPermissionsMixin, ScheduleAdmin):
    pass


class MyTaskAdmin(NoPermissionsMixin, TaskAdmin):
    pass


class MyFailAdmin(NoPermissionsMixin, FailAdmin):
    pass


class MyQueueAdmin(NoPermissionsMixin, QueueAdmin):
    pass


admin.site.unregister(Schedule)
admin.site.unregister(Success)
admin.site.unregister(Failure)
admin.site.unregister(OrmQ)
admin.site.register(Schedule, MyScheduleAdmin)
admin.site.register(Success, MyTaskAdmin)
admin.site.register(Failure, MyFailAdmin)
admin.site.register(OrmQ, MyQueueAdmin)
