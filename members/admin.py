from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse, path
from django.utils import timezone

from members.models import User, QGroup, Person, Instrument, Key, GSuiteAccount, ExternalCard, Membership, \
    ExternalCardLoan


class QAdmin(admin.AdminSite):
    site_header = "ESMG Quadrivium"


admin_site = QAdmin()
admin_site.register(User, UserAdmin)


# External card thingies

class ExternalCardLoanInline(admin.TabularInline):
    """External card loan inline, for person and external card admin pages."""
    model = ExternalCardLoan
    extra = 0
    fields = ('external_card', 'person', 'start', 'end', 'deposit_made')
    readonly_fields = ()
    autocomplete_fields = ('person',)
    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ExternalCardLoan, site=admin_site)
class ExternalCardLoanAdmin(admin.ModelAdmin):
    """Separate admin page for external card loans."""
    list_display = ('external_card', 'person', 'start', 'end')
    fields = ('external_card', 'person', 'start', 'end', 'deposit_made')
    autocomplete_fields = ('person',)

    def get_readonly_fields(self, request, obj=None):
        """External card, person and start date are only editable during creation."""
        if obj:
            return 'external_card', 'person', 'start'
        else:
            return ()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ExternalCard, site=admin_site)
class ExternalCardAdmin(admin.ModelAdmin):
    """Admin page for external cards."""
    fields = ('card_number', 'reference_number', 'description')
    inlines = (ExternalCardLoanInline,)


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


# Group membership inline thingies

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
    autocomplete_fields = ('owner',)
    inlines = (MembershipChangeInline, MembershipAddInline)


@admin.register(Person, site=admin_site)
class PersonAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('username', ('first_name', 'last_name'), 'initials', 'created_at')
        }),
        ('Contact details', {
            'fields': ('email', 'phone_number', 'street', 'postal_code', 'city', 'country')
        }),
        ('Personal details', {
            'fields': ('gender', 'date_of_birth', 'preferred_language', 'instruments', 'field_of_study')
        }),
        ('Quadrivium', {
            'fields': ('person_id', 'is_student', ('iban', 'sepa_direct_debit'),
                       'bhv_certificate', 'gsuite_accounts', 'notes')
        }),
        ('TU/e', {
            'fields': ('tue_card_number', 'key_access', ('keywatcher_id', 'keywatcher_pin'))
        }),
    )
    readonly_fields = ('created_at',)
    list_display = ('username', 'email', 'first_name', 'last_name')
    list_filter = (GroupFilter,)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('instruments', 'gsuite_accounts', 'key_access')
    inlines = (MembershipChangeInline, MembershipAddInline, ExternalCardLoanInline)
    save_on_top = True

    # def lookup_allowed(self, lookup, value):
    #     # Don't allow lookups involving passwords.
    #     return not lookup.startswith('password') and super().lookup_allowed(lookup, value)

    def get_urls(self):
        # Add unsubscribe URL
        urls = super().get_urls()
        custom_url = [
            path('<int:person_id>/unsubscribe/',
                 self.admin_site.admin_view(self.unsubscribe_view),
                 name='members_person_unsubscribe',
                 ),

        ]
        return custom_url + urls

    def unsubscribe_view(self, request, person_id, *args, **kwargs):
        person = self.get_object(request, person_id)
        if person is None:
            self.message_user(request, 'Person with ID “{}” doesn’t exist.'.format(person_id), messages.WARNING)
            return HttpResponseRedirect(reverse('admin:index'))

        if not self.has_change_permission(request, person):
            raise PermissionDenied

        memberships_removed = Membership.objects.filter(person=person, end=None, group__end_on_unsubscribe=True)
        memberships_kept = Membership.objects.filter(person=person, end=None, group__end_on_unsubscribe=False)
        if request.POST:
            # Do actual unsubscribe
            # Pick memberships that are not ended and are for groups that have `end on unsubscribe==True`
            for membership in memberships_removed:
                membership.end = timezone.now()
                membership.save()
            self.message_user(request,
                              'Person “{}” has been removed from the internal groups.'.format(person.get_full_name()),
                              messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:members_person_change', args=(person.pk,)))

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': 'Unsubscribe person',
            'object': person,
            'memberships_removed': memberships_removed,
            'memberships_kept': memberships_kept,
            'keys': [k.number for k in person.key_access.all()]  # Would be nicer to have this in template only
        }
        return TemplateResponse(request, 'admin/members/person/unsubscribe.html', context)


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
