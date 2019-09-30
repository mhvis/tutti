from django.contrib import admin

# Register your models here.
from ldapproxy.models import ObjectClassMapping, AttributeMapping, LdapEntry, LdapEntryObjectClasses

admin.site.register((ObjectClassMapping,
                     AttributeMapping,
                     LdapEntry,
                     LdapEntryObjectClasses))
