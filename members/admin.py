from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse, path
from django.utils import timezone

from members.models import User, QGroup, Person, Instrument, Key, GSuiteAccount, ExternalCard, \
    ExternalCardLoan, GroupMembership


class QAdmin(admin.AdminSite):
    site_header = "ESMG Quadrivium"


admin_site = QAdmin()
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)


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


class UserGroupFormSet(forms.BaseInlineFormSet):
    """Form for user/group inline that updates historical records (GroupMembership model)."""
    def save_new(self, form, commit=True):
        # Whenever a new group entry is added, also store a new history record
        instance = super().save_new(form, commit)
        if commit:
            GroupMembership.objects.create(group=instance.group, user=instance.user)
        return instance

    def delete_existing(self, obj, commit=True):
        # Whenever a group entry is removed, set the end date on history record
        super().delete_existing(obj, commit)
        if commit:
            membership = GroupMembership.objects.get(group=obj.group, user=obj.user, end=None)
            membership.end = timezone.now()
            membership.save()


class UserGroupModelForm(forms.ModelForm):
    """Filter user/group form for only User instances which have a linked Person instance.

    Note that all users will still be shown in the form, but it's not possible
    to save a form with invalid Person instances.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(person__isnull=False)


class UserGroupInline(admin.TabularInline):
    """Inline for user/group relations (group memberships)."""

    model = User.groups.through
    extra = 0
    autocomplete_fields = ('user', 'group')
    verbose_name = 'group membership'
    verbose_name_plural = 'group memberships'
    formset = UserGroupFormSet
    form = UserGroupModelForm

    def has_change_permission(self, request, obj=None):
        # Can only add or delete
        return False


@admin.register(QGroup, site=admin_site)
class QGroupAdmin(GroupAdmin):
    # search_fields = ('name',)
    # ordering = ('name',)

    autocomplete_fields = ('owner',)
    fields = ('name', 'description', 'email', 'end_on_unsubscribe', 'owner', 'permissions',)
    inlines = (UserGroupInline,)


@admin.register(Person, site=admin_site)
class PersonAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('username', ('first_name', 'last_name'), 'initials', 'email', 'groups')
        }),
        ('Contact details', {
            'fields': ('phone_number', 'street', 'postal_code', 'city', 'country')
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
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined')
    list_display = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('groups',)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('instruments', 'gsuite_accounts', 'key_access', 'groups')

    inlines = (ExternalCardLoanInline,)
    save_on_top = True

    def lookup_allowed(self, lookup, value):
        # Don't allow lookups involving passwords.
        return not lookup.startswith('password') and super().lookup_allowed(lookup, value)

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
        """View for person unsubscribed, removes the person from groups on POST."""
        person = self.get_object(request, person_id)  # type: Person
        if person is None:
            self.message_user(request, 'Person with ID “{}” doesn’t exist.'.format(person_id), messages.WARNING)
            return HttpResponseRedirect(reverse('admin:index'))

        if not self.has_change_permission(request, person):
            raise PermissionDenied

        groups_removed = person.groups.filter(qgroup__end_on_unsubscribe=True)
        groups_kept = person.groups.difference(groups_removed)
        if request.POST:
            # Do actual group removal
            person.groups.remove(*groups_removed)
            self.message_user(request,
                              'Person “{}” has been removed from the internal groups.'.format(person.get_full_name()),
                              messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:members_person_change', args=(person.pk,)))

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': 'Unsubscribe person',
            'object': person,
            'groups_removed': groups_removed,
            'groups_kept': groups_kept,
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


@admin.register(GroupMembership, site=admin_site)
class GroupMembershipAdmin(admin.ModelAdmin):
    """(Historical) memberships can only be viewed here, not modified."""
    list_display = ('user', 'group', 'current', 'start', 'end')
    # list_display_links = None
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
