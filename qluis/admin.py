from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group as DjangoGroup

from qluis.models import User, Group, Person, Instrument, Key, GSuiteAccount, ExternalCard

admin.site.register(User, UserAdmin)
admin.site.unregister(DjangoGroup)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    fields = ('username', 'first_name', 'last_name', 'email', 'groups',
              'initials', 'street', 'postal_code', 'city', 'phone_number',
              'preferred_language',
              'tue_card_number',
              'date_of_birth',
              'gender',
              'is_student',
              'membership_start',
              'membership_end',
              'permission_exquus',
              'sepa_direct_debit',
              'instruments',
              'bhv_certificate',
              'external_card',
              'external_card_deposit_made',
              'field_of_study',
              'found_via',
              'gsuite_accounts',
              'iban',
              'person_id',
              'key_access',
              'keywatcher_id',
              'keywatcher_pin'

              )
    list_display = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('groups',)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'instruments', 'gsuite_accounts', 'key_access')

    def lookup_allowed(self, lookup, value):
        # Don't allow lookups involving passwords.
        return not lookup.startswith('password') and super().lookup_allowed(lookup, value)


admin.site.register(Instrument)
admin.site.register(Key)
admin.site.register(GSuiteAccount)
admin.site.register(ExternalCard)
