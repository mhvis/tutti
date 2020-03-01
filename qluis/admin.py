from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group as DjangoGroup

from qluis.models import User, Group, Person, Instrument, Key, GSuiteAccount, ExternalCard, Membership


class QAdmin(admin.AdminSite):
    site_header = "ESMG Quadrivium"


admin_site = QAdmin()
admin_site.register(User, UserAdmin)
admin.site.unregister(DjangoGroup)


class GroupFilter(admin.SimpleListFilter):
    title = 'Groups'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        return [(group.id, group.name) for group in Group.objects.all()]

    def queryset(self, request, queryset):
        value = self.value()
        if value is None:
            return queryset.all()
        return queryset.filter(membership__group__id=value)


class MembershipAdminInline(admin.TabularInline):
    model = Membership
    can_delete = False

    def get_queryset(self, request):
        qs = super(MembershipAdminInline, self).get_queryset(request)
        return qs.filter(end=None)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)
    inlines = (MembershipAdminInline,)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    fields = ('username', 'first_name', 'last_name', 'email',
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
    list_filter = (GroupFilter,)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('instruments', 'gsuite_accounts', 'key_access')
    inlines = (MembershipAdminInline,)

    def lookup_allowed(self, lookup, value):
        # Don't allow lookups involving passwords.
        return not lookup.startswith('password') and super().lookup_allowed(lookup, value)


admin_site.register(Group)
admin_site.register(Person)
admin_site.register(Instrument)
admin_site.register(Key)
admin_site.register(GSuiteAccount)
admin_site.register(ExternalCard)
