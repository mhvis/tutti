"""Use Django signals to automatically run sync on object changes."""

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
    async_task('sync.ldapsync.ldap_sync')


@receiver(post_migrate)
def setup_sync_tasks(sender, **kwargs):
    """Sets up the sync tasks which will be run using Django Q."""
    # (Re)create LDAP sync task
    Schedule.objects.filter(name='ldapsync').delete()
    # Because syncs will also run after each modification in the database, I
    #  use a daily schedule instead of something shorter.
    schedule('sync.ldapsync.ldap_sync',
             name='ldapsync',
             schedule_type=Schedule.DAILY)
