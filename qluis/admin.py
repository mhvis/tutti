from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone

from qluis.models import User, QGroup, Person, Instrument, Key, GSuiteAccount, ExternalCard, Membership


class QAdmin(admin.AdminSite):
    site_header = "ESMG Quadrivium"


admin_site = QAdmin()
admin_site.register(User, UserAdmin)


class GroupFilter(admin.SimpleListFilter):
    """Filter for group membership."""

    title = 'groups'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        return [(group.id, group.name) for group in QGroup.objects.all()]

    def queryset(self, request, queryset):
        value = self.value()
        if value and QGroup.objects.filter(id=value).exists():
            return queryset.filter(membership__end=None, membership__group=value)


class MembershipForm(forms.ModelForm):
    """This form extension adds a boolean field for ending a membership."""

    end_now = forms.BooleanField(label='end?', required=False)

    def clean(self):
        """Set end value to current time if boolean checkbox is checked."""
        cleaned_data = super().clean()
        if cleaned_data.get('end_now') is True:
            self.instance.end = timezone.now()
        return cleaned_data


# Genius workaround, thanks to https://stackoverflow.com/a/28149575/2373688

class MembershipChangeInline(admin.TabularInline):
    """Inline for changing (ending) group membership."""

    model = Membership
    fields = ('group', 'person', 'start', 'end_now')
    readonly_fields = ('group', 'person', 'start',)

    # MembershipForm allows for ending group membership using end_now field
    form = MembershipForm

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # Filter for current memberships
        qs = super().get_queryset(request)
        return qs.filter(end=None)


class MembershipAddInline(admin.TabularInline):
    """Inline for adding a new group membership."""

    model = Membership
    fields = ('group', 'person', 'start')
    readonly_fields = ('start',)
    extra = 0
    verbose_name_plural = 'add new memberships'
    autocomplete_fields = ('person',)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return False


@admin.register(QGroup, site=admin_site)
class QGroupAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)
    inlines = (MembershipChangeInline, MembershipAddInline)


@admin.register(Person, site=admin_site)
class PersonAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('username', 'first_name', 'last_name', 'initials')
        }),
        ('Contact details', {
            'fields': ('email', 'phone_number', 'street', 'postal_code', 'city')
        }),
        ('Misc', {
            'fields': ('gender', 'date_of_birth', 'preferred_language', 'field_of_study')
        }),
        ('Quadrivium specific', {
            'fields': ('tue_card_number', 'is_student', 'sepa_direct_debit', 'instruments', 'bhv_certificate',
                       'external_card', 'external_card_deposit_made', 'gsuite_accounts', 'iban', 'person_id',
                       'key_access', 'keywatcher_id', 'keywatcher_pin')
        })
    )

    list_display = ('email', 'first_name', 'last_name')
    list_filter = (GroupFilter,)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('instruments', 'gsuite_accounts', 'key_access')
    inlines = (MembershipChangeInline, MembershipAddInline)
    save_on_top = True

    # def lookup_allowed(self, lookup, value):
    #     # Don't allow lookups involving passwords.
    #     return not lookup.startswith('password') and super().lookup_allowed(lookup, value)


class CurrentMembershipListFilter(admin.SimpleListFilter):
    """Filter for current group memberships."""

    title = 'current'
    parameter_name = 'current'

    def lookups(self, request, model_admin):
        return (('y', 'Only current'),
                ('n', 'Only past'))

    def queryset(self, request, queryset):
        if self.value() == 'y':
            return queryset.filter(end=None)
        if self.value() == 'n':
            return queryset.filter(end__isnull=False)


@admin.register(Membership, site=admin_site)
class MembershipAdmin(admin.ModelAdmin):
    """Memberships can only be viewed here, not modified."""
    list_display = ('person', 'group', 'current', 'start', 'end')
    list_display_links = None
    list_filter = (CurrentMembershipListFilter, 'group')

    short_description = 'haai'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def current(self, obj):
        return obj.end is None

    current.boolean = True


admin_site.register(Instrument)
admin_site.register(Key)
admin_site.register(GSuiteAccount)
admin_site.register(ExternalCard)
