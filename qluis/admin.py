from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group as DjangoGroup

from django.utils.html import format_html
from django.urls import reverse

from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from qluis.models import User, Group, Person, Instrument, Key, GSuiteAccount, ExternalCard, Membership

admin.site.register(User, UserAdmin)
admin.site.unregister(DjangoGroup)


class GroupFilter(admin.SimpleListFilter):
    title = 'Groups'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        return [(group.id, group.name) for group in Group.objects.all()]

    def queryset(self, request, queryset):
        value = self.value()
        if value == None:
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

    def get_urls(self):
        urls = super().get_urls()
        custom_url = [
            url(r'^(?P<person_id>.+)/person_unsubscribe/$',
                self.unsubscribe,
                name='person-unsubscribe',
            ),
        ]
        return custom_url + urls

    def person_actions(self, obj):
        if obj.membership_end == None:
            return format_html(
                '<a class="button" href="{}">Unsubscribe</a>',
                reverse('admin:person-unsubscribe', args=[obj.pk]),
            )
        else:
            return ''
    person_actions.short_description = 'Actions'
    person_actions.allow_tags = True

    def unsubscribe(self, request, person_id, *args, **kwargs):
        person = self.get_object(request, person_id)
        if request.method == 'POST':
            person.unsubscribe()
            return HttpResponseRedirect('../../')
        title = '%s %s (%s)' % (person.first_name, person.last_name, person.username)

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['title'] = title
        context['groups'] = ['Huidige leden', 'Bestuur']
        context['exquus'] = person.permission_exquus
        context['email'] = person.email
        return TemplateResponse(
            request,
            'admin/person/unsubscribe.html',
            context,
        )


admin.site.register(Instrument)
admin.site.register(Key)
admin.site.register(GSuiteAccount)
admin.site.register(ExternalCard)
