"""Extra admin models for Django Q job scheduler."""
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


def register_job_queue_admin(admin_site):
    """Register admin models for the job queue."""
    # Set up Django Q admin integration
    admin_site.register(Schedule, MyScheduleAdmin)
    admin_site.register(Success, MyTaskAdmin)
    admin_site.register(Failure, MyFailAdmin)
    admin_site.register(OrmQ, MyQueueAdmin)
