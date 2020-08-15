from django import forms
from django.contrib import admin, messages
from django.contrib.admin import RelatedFieldListFilter
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.forms import UserChangeForm, AdminPasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.template.response import TemplateResponse
from django.urls import reverse, path
from import_export.admin import ImportExportMixin

from members.adminjobqueue import register_job_queue_admin
from members.adminresources import PersonResource
from members.models import User, QGroup, Person, Instrument, Key, GSuiteAccount, ExternalCard, \
    ExternalCardLoan, GroupMembership, PersonTreasurerFields


class QAdmin(admin.AdminSite):
    site_header = "Members admin"
    site_title = "Tutti"
    index_title = "Members admin"

    def has_permission(self, request):
        # Allow everyone to access the admin site (normally the user needs to be staff)
        #  Users will need to have explicit permissions assigned in order to be able to do something
        return request.user.is_active


admin_site = QAdmin()
register_job_queue_admin(admin_site)
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


# Group membership inlines

class GroupMembershipInline(admin.TabularInline):
    """Inline for viewing group memberships."""
    model = GroupMembership
    fields = ('group', 'user', 'start', 'end')

    # ordering = ('end', 'start')  # Todo optionally specify ordering

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CurrentGroupMembershipInline(GroupMembershipInline):
    """Inline for viewing current group memberships."""
    fields = ('group', 'user', 'start')

    def get_queryset(self, request):
        # Filter for memberships without end date
        return super().get_queryset(request).filter(end=None)


# QGroup

class QGroupModelForm(forms.ModelForm):
    """Group form with a field for group members.

    We can't directly use the `user_set` attribute from the `User.groups`
    attribute because it is linked to the `Group` model and not to `QGroup`.
    Therefore we need to use a custom field.
    """

    group_members = forms.ModelMultipleChoiceField(
        queryset=Person.objects.all(),
        widget=FilteredSelectMultiple(
            verbose_name='people',
            is_stacked=False),  # Horizontal widget
        required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # When creating a new group, this will be False
            self.fields['group_members'].initial = self.instance.user_set.all()

    def _save_m2m(self):
        """See superclass method, additionally saves the group members."""
        # A bit ugly to override the private method _save_m2m here.
        # Alternatively it is possible to wrap the save_m2m function from the
        # superclass but that is way more verbose.
        super()._save_m2m()
        self.instance.user_set.set(self.cleaned_data['group_members'])

    class Meta:
        fields = ('group_members',)
        model = QGroup
        help_texts = {
            "name": "Can't be changed after creation. To change a group name, create a new group."
        }


@admin.register(QGroup, site=admin_site)
class QGroupAdmin(GroupAdmin):
    form = QGroupModelForm

    fields = ('name', 'description', 'email', 'end_on_unsubscribe', 'owner', 'group_members', 'permissions')
    autocomplete_fields = ('owner',)

    inlines = (CurrentGroupMembershipInline,)

    def get_readonly_fields(self, request, obj=None):
        """Makes name field readonly.

        This is because name changes do not propagate correctly to SharePoint.
        Instead it is better to recreate a group to change the name.
        """
        if obj:
            return ["name"]
        else:
            return []


# Person

class GroupListFilter(RelatedFieldListFilter):
    """Filter that orders the groups on the `name` field."""

    def field_admin_ordering(self, field, request, model_admin):
        return ('name',)


class PersonAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('username', "password")
        }),
        ("Personal info", {
            "fields": (('first_name', 'last_name'), 'initials', 'email', 'groups')
        }),
        ('Contact details', {
            'fields': ('phone_number', 'street', 'postal_code', 'city', 'country')
        }),
        ('Personal info', {
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
    list_filter = (('groups', GroupListFilter),)  # Custom group filter that applies ordering
    search_fields = ('username', 'first_name', 'last_name', 'email',
                     'initials', 'phone_number',
                     'street', 'postal_code', 'city',
                     'person_id', 'iban', 'notes')
    ordering = ('username',)
    filter_horizontal = ('instruments', 'gsuite_accounts', 'key_access', 'groups')

    inlines = (ExternalCardLoanInline, GroupMembershipInline)
    save_on_top = True

    form = UserChangeForm  # Needed for the username and password fields/widgets

    # Needed for UserAdmin.user_change_password
    change_password_form = AdminPasswordChangeForm
    change_user_password_template = None

    def lookup_allowed(self, lookup, value):
        # Don't allow lookups involving passwords.
        # return not lookup.startswith('password') and super().lookup_allowed(lookup, value)
        # But do allow the rest, so that we can create some cool queries in the address bar
        return not lookup.startswith('password')

    def get_urls(self):
        # Add unsubscribe URL
        return [path('<id>/unsubscribe/',
                     self.admin_site.admin_view(self.unsubscribe_view),
                     name='members_person_unsubscribe',
                     ),
                path('<id>/password/',
                     # Trick from here: https://stackoverflow.com/a/1015405
                     self.admin_site.admin_view(UserAdmin.user_change_password.__get__(self, PersonAdmin)),
                     name='members_person_password_change',
                     ),
                ] + super().get_urls()

    def unsubscribe_view(self, request, id, *args, **kwargs):
        """View for person unsubscribed, removes the person from groups on POST."""
        person = self.get_object(request, id)  # type: Person
        if not self.has_change_permission(request, person):
            raise PermissionDenied
        if person is None:
            raise Http404

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

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Password can only be set after creation.
        # Kinda ugly but we need to always change the object because we change the original instance variable
        fieldsets[0][1]["fields"] = ("username",) if not obj else ("username", "password")
        return fieldsets


@admin.register(Person, site=admin_site)
class PersonImportExportAdmin(ImportExportMixin, PersonAdmin):
    """PersonAdmin extended with import/export capabilities."""
    resource_class = PersonResource  # Import/export settings

    def has_import_permission(self, request):
        # Only allow import if user has change+add+delete permission
        return request.user.has_perms(['members.add_person', 'members.change_person', 'members.delete_person'])

    def has_export_permission(self, request):
        return request.user.has_perm('members.view_person')


@admin.register(PersonTreasurerFields, site=admin_site)
class PersonTreasurerFieldsAdmin(admin.ModelAdmin):
    """Separate admin for specific treasurer fields only."""
    fields = ("username", 'person_id', 'is_student', 'iban', 'sepa_direct_debit',)
    readonly_fields = ("username",)
    list_display = ('username', 'first_name', 'last_name', 'email')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin_site.register(Instrument)
admin_site.register(Key)


class GSuiteAccountInline(admin.TabularInline):
    model = Person.gsuite_accounts.through
    extra = 0
    autocomplete_fields = ('person',)
    verbose_name = 'authorized person'
    verbose_name_plural = 'authorized people'

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(GSuiteAccount, site=admin_site)
class GSuiteAccountAdmin(admin.ModelAdmin):
    fields = ('email',)
    inlines = (GSuiteAccountInline,)
