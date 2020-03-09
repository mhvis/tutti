from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from qluis.models import User, QGroup, Person, Instrument, Key, GSuiteAccount, ExternalCard, Membership


class QAdmin(admin.AdminSite):
    site_header = "ESMG Quadrivium"


admin_site = QAdmin()
admin_site.register(User, UserAdmin)


# The code below needs comments or needs to be rewritten to be more clear
class GroupFilter(admin.SimpleListFilter):
    title = 'Groups'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        return [(group.id, group.name) for group in QGroup.objects.all()]

    def queryset(self, request, queryset):
        value = self.value()
        if value is None:
            return queryset.all()
        return queryset.filter(membership__group__id=value)


class MembershipInline(admin.TabularInline):
    """Inline for group membership, used on Person and Group model pages."""

    model = Membership
    fields = ('group', 'person', 'start')
    readonly_fields = ('start',)
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # Only current memberships are picked, not historic
        qs = super().get_queryset(request)
        return qs.filter(end=None)


class QGroupAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)
    inlines = (MembershipInline,)


class PersonAdmin(admin.ModelAdmin):
    fields = ('username',
              'first_name',
              'last_name',
              'email',
              'initials',
              'street',
              'postal_code',
              'city',
              'phone_number',
              'preferred_language',
              'tue_card_number',
              'date_of_birth',
              'gender',
              'is_student',
              'sepa_direct_debit',
              'instruments',
              'bhv_certificate',
              'external_card',
              'external_card_deposit_made',
              'field_of_study',
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
    inlines = (MembershipInline,)

    # def lookup_allowed(self, lookup, value):
    #     # Don't allow lookups involving passwords.
    #     return not lookup.startswith('password') and super().lookup_allowed(lookup, value)


admin_site.register(QGroup, QGroupAdmin)
admin_site.register(Person, PersonAdmin)
admin_site.register(Instrument)
admin_site.register(Key)
admin_site.register(GSuiteAccount)
admin_site.register(ExternalCard)
admin_site.register(Membership)