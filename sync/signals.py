"""Use Django signals to automatically run sync on object changes."""
from django.conf import settings
from django.db.models.signals import post_save, post_delete, post_migrate
from django.dispatch import receiver
from django_q.models import Schedule
from django_q.tasks import schedule, async_task

from members.models import Person, QGroup


@receiver(post_save, sender=Person)
@receiver(post_save, sender=QGroup)
@receiver(post_delete, sender=Person)
@receiver(post_delete, sender=QGroup)
def queue_sync(sender, **kwargs):
    """Queues a sync task to be run immediately."""
    if settings.LDAP_SYNC_ON_SAVE:
        async_task("sync.ldapsync.ldap_sync")
    if settings.GRAPH_SYNC_ON_SAVE:
        async_task("sync.aad.tasks.aad_sync")


def migrate_schedule(func, name, version: int, *args, **kwargs):
    """Whenever the version number is incremented by 1, recreates the schedule.

    Args:
        func: See schedule().
        name: See schedule().
        version: Version schedule number, start with 1 and increment each time
            the schedule is changed.
        *args: See schedule().
        **kwargs: See schedule().
    """
    # Delete earlier versions
    earlier_names = ["{}-{}".format(name, i) for i in range(1, version)]
    Schedule.objects.filter(name__in=earlier_names).delete()
    # Create current version if it doesn't exist
    current_name = "{}-{}".format(name, version)
    if not Schedule.objects.filter(name=current_name).exists():
        schedule(func, name=current_name, *args, **kwargs)


@receiver(post_migrate)
def setup_sync_tasks(sender, **kwargs):
    """Sets up the sync tasks which will be run using Django Q."""
    # No-op, todo: remove after it has been applied
    Schedule.objects.filter(name='ldapsync').delete()
    # Because syncs will also run after each modification in the database, I
    #  use a daily schedule instead of something shorter.

    # Schedule for LDAP
    migrate_schedule(func="sync.ldapsync.ldap_sync",
                     name="ldapsync",
                     version=1,
                     schedule_type=Schedule.DAILY)
    # Schedule for AAD
    migrate_schedule(func="sync.aad.tasks.aad_sync",
                     name="aadsync",
                     version=1,
                     schedule_type=Schedule.DAILY)
