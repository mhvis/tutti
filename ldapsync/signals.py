from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from members.models import Person


# TODO! We can use these signals to automatically add or delete entries in LDAP
#  whenever a new entry is created here.

@receiver(pre_save, sender=Person)
def person_save(sender, instance: Person, created: bool, **kwargs):
    pass


@receiver(pre_delete, sender=Person)
def person_delete(sender, instance: Person, **kwargs):
    pass
