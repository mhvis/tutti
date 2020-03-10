from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.forms import BaseInlineFormSet
from django.utils.safestring import mark_safe

from qluis.models import User, QGroup, Person, Instrument, Key, GSuiteAccount, ExternalCard, Membership


class QAdmin(admin.AdminSite):
    site_header = "ESMG Quadrivium"


admin_site = QAdmin()
admin_site.register(User, UserAdmin)


class GroupFilter(admin.SimpleListFilter):
    """Filter for group membership.

    # TODO: I don't that this filters for memberships without end date.
    """
    title = 'Groups'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        return [(group.id, group.name) for group in QGroup.objects.all()]

    def queryset(self, request, queryset):
        value = self.value()
        if value is None:
            return queryset.all()
        return queryset.filter(membership__group__id=value)


# TODO: tryout class, to be removed
class MembershipInlineFormSet(BaseInlineFormSet):

    def save_existing(self, form, instance, commit=True):
        print('save existing: {} {} {}'.format(form, instance, commit))
        return super().save_existing(form, instance, commit)

    def save(self, commit=True):
        print('MembershipInlineFormSet.save called on: {}'.format(self))
        return super().save(commit)


# TODO: tryout class, to be removed
class MembershipForm(forms.ModelForm):

    def save(self, commit=True):
        print('MembershipForm.save called on: {}'.format(self))
        return super().save(commit)


class MembershipInline(admin.TabularInline):
    """Inline for group membership, used on Person and Group model pages."""

    model = Membership
    fields = ('group', 'person', 'start', 'end_now')
    readonly_fields = ('start', 'end_now')
    # TODO: tryout, to be removed
    form = MembershipForm
    # TODO: tryout, to be removed
    formset = MembershipInlineFormSet
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # Filter for current memberships
        qs = super().get_queryset(request)
        return qs.filter(end=None)

    def end_now(self, obj):
        if obj.pk:
            return mark_safe(
                '<form action="" method="post"><button type="submit" class="button">End now</button></form>')
        else:
            return ''


@admin.register(QGroup, site=admin_site)
class QGroupAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)
    inlines = (MembershipInline,)


@admin.register(Person, site=admin_site)
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
    list_display = ('email', 'first_name', 'last_name')
    list_filter = (GroupFilter,)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('instruments', 'gsuite_accounts', 'key_access')
    inlines = (MembershipInline,)

    # def lookup_allowed(self, lookup, value):
    #     # Don't allow lookups involving passwords.
    #     return not lookup.startswith('password') and super().lookup_allowed(lookup, value)


@admin.register(Membership, site=admin_site)
class MembershipAdmin(admin.ModelAdmin):
    """Memberships can only be viewed here, not modified."""
    list_display = ('person', 'group', 'start', 'end')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin_site.register(Instrument)
admin_site.register(Key)
admin_site.register(GSuiteAccount)
admin_site.register(ExternalCard)
