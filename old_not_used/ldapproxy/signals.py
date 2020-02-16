from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from ldapproxy.models import LdapEntry, ObjectClassMapping
from tutti.models import Member

# Todo: move to settings file
BASE_DN = 'dc=esmgquadrivium,dc=nl'


@receiver(post_save, sender=Member)
def create_member_entry(sender, instance: Member, created: bool, **kwargs):
    if not created:
        return
    dn = 'cn={},{}'.format(instance.get_full_name(), BASE_DN)
    oc_mapping = ObjectClassMapping.objects.get(key_table=Member._meta.db_table)

    LdapEntry.objects.create(dn=dn,
                             object_class_mapping=oc_mapping,
                             key_value=instance.id)


@receiver(pre_delete, sender=Member)
def delete_member_entry(sender, instance: Member, **kwargs):
    oc_mapping = ObjectClassMapping.objects.get(key_table=Member._meta.db_table)

    entry = LdapEntry.objects.get(object_class_mapping=oc_mapping,
                                  key_value=instance.id)
    entry.delete()
