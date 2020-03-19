from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils import timezone

from members.models import Person, GroupMembership, User


@receiver(m2m_changed, sender=Person.groups.through)
def record_group_membership(sender, instance, action, reverse, model, pk_set, **kwargs):
    """When the groups fields on User model has changed, keep a record of the change."""
    if action == "post_add":
        if not reverse:
            user = instance
            for group_pk in pk_set:
                group = Group.objects.get(pk=group_pk)
                GroupMembership.objects.create(group=group, user=user)
        else:
            group = instance
            for user_pk in pk_set:
                user = User.objects.get(pk=user_pk)
                GroupMembership.objects.create(group=group, user=user)
    elif action == "post_remove":
        if not reverse:
            user = instance
            for group_pk in pk_set:
                group = Group.objects.get(pk=group_pk)
                membership = GroupMembership.objects.get(group=group, user=user, end=None)
                membership.end = timezone.now()
                membership.save()
        else:
            group = instance
            for user_pk in pk_set:
                user = User.objects.get(pk=user_pk)
                membership = GroupMembership.objects.get(group=group, user=user, end=None)
                membership.end = timezone.now()
                membership.save()
