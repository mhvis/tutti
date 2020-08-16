from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, UserManager
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from ldap3 import HASHED_SALTED_SHA512
from ldap3.utils.hashed import hashed
from localflavor.generic.models import IBANField
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """A user for authentication and groups, optionally linked to a Person."""

    ldap_password = models.CharField(max_length=256, default="")
    """Stores the password hashed in a format that LDAP understands.

    A bit invasive, but an easy solution.
    """

    def __str__(self):
        # Default implementation returns username
        return self.get_full_name()

    def set_password(self, raw_password):
        # Hook into the password system for creating an additional hash for use
        # with LDAP.
        super().set_password(raw_password)
        self.ldap_password = hashed(HASHED_SALTED_SHA512, raw_password)


class Instrument(models.Model):
    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class QGroupManager(models.Manager):
    pass
    # def get_members_group(self):
    #     """Returns the current members group.
    #
    #     If you just need the ID for filtering, use settings.MEMBERS_GROUP.
    #     """
    #     return self.get(id=settings.MEMBERS_GROUP)


class QGroup(Group):
    """Extension of the Group model for Quadrivium fields."""
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True, verbose_name='e-mail')
    end_on_unsubscribe = models.BooleanField(default=True,
                                             help_text=('If set, when a person is unsubscribed they are removed '
                                                        'from this group.'))
    owner = models.ForeignKey('Person',
                              on_delete=models.PROTECT,
                              null=True,
                              blank=True,
                              help_text='E.g. the commissioner.')

    objects = QGroupManager()

    class Meta:
        verbose_name = 'group'
        verbose_name_plural = 'groups'


class ExternalCard(models.Model):
    card_number = models.IntegerField(null=True,
                                      blank=True,
                                      help_text="7-digit (usually) card identifier number.")
    reference_number = models.IntegerField(null=True,
                                           blank=True,
                                           help_text='Short reference number written on the card.')
    description = models.CharField(max_length=150,
                                   help_text='Additional indication that is written on the card.',
                                   blank=True)

    # decommissioned = models.BooleanField for when a card is no longer used by Q?

    def __str__(self):
        return '–'.join([str(x) for x in (self.card_number, self.reference_number, self.description) if x])


class GSuiteAccount(models.Model):
    class Meta:
        verbose_name = 'G Suite account'

    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email


class Key(models.Model):
    number = models.IntegerField(primary_key=True)
    room_name = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return '{} {}'.format(self.number, self.room_name).strip()


class PersonQuerySet(QuerySet):
    def filter_members(self):
        """Filters people that are currently a member."""
        if settings.MEMBERS_GROUP == -1:
            # Members group ID not set, do nothing
            return self
        return self.filter(groups=settings.MEMBERS_GROUP)


class PersonManager(UserManager.from_queryset(PersonQuerySet)):
    pass


class Person(User):
    """Extends a user with Quadrivium related fields.

    We extend User (instead of a separate model) so that we can use the
    built-in groups field for group membership and make use of the permissions
    system that comes with it. The user account does not need to have a
    password set or be active.
    """

    class Meta:
        verbose_name = 'person'
        verbose_name_plural = 'people'
        permissions = [
            ('change_treasurer_fields', 'Can change treasurer related fields'),
        ]

    objects = PersonManager()

    initials = models.CharField(max_length=30, blank=True)

    # Address
    street = models.CharField(max_length=150, blank=True)
    postal_code = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=150, blank=True)
    country = CountryField(blank=True, default='NL')

    phone_number = PhoneNumberField(blank=True)

    PREFERRED_LANGUAGES = (
        ('en-us', 'English'),
        ('nl-nl', 'Dutch'),
    )
    preferred_language = models.CharField(max_length=30,
                                          blank=True,
                                          choices=PREFERRED_LANGUAGES)
    tue_card_number = models.IntegerField(null=True,
                                          blank=True,
                                          verbose_name='TU/e card number')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=30,
                              blank=True,
                              choices=(('male', 'Male'), ('female', 'Female')))
    is_student = models.BooleanField(null=True, blank=True)

    sepa_direct_debit = models.BooleanField(null=True,
                                            blank=True,
                                            verbose_name='SEPA direct debit')

    instruments = models.ManyToManyField(Instrument, blank=True)

    bhv_certificate = models.DateField(null=True,
                                       blank=True,
                                       verbose_name='BHV certificate date')

    field_of_study = models.CharField(max_length=150,
                                      blank=True)

    gsuite_accounts = models.ManyToManyField(GSuiteAccount,
                                             blank=True,
                                             verbose_name='G Suite accounts')

    iban = IBANField(blank=True, verbose_name='IBAN')
    person_id = models.CharField(max_length=30, blank=True, verbose_name='person ID', help_text='Davilex code.')

    key_access = models.ManyToManyField(Key, blank=True)
    keywatcher_id = models.CharField(max_length=4, blank=True, verbose_name='KeyWatcher ID')
    keywatcher_pin = models.CharField(max_length=4, blank=True, verbose_name='KeyWatcher PIN')

    notes = models.TextField(blank=True)

    def current_external_card_loans(self):
        """Get current external card loans."""
        return self.externalcardloan_set.filter(end=None)

    def is_member(self):
        """Returns whether this person is currently a member."""
        return self.groups.filter(id=settings.MEMBERS_GROUP).exists()

    is_member.boolean = True  # This attribute enables a pretty on/off icon in Django admin


class PersonTreasurerFields(Person):
    """Person proxy for use in admin for treasurer fields, see admin.py."""

    class Meta:
        proxy = True
        verbose_name_plural = "people treasurer fields"


class GroupMembership(models.Model):
    """Group membership records, including historical memberships.

    There's a separate table (groups field on a User) which stores the current
    group memberships. This table stores those as well but also includes group
    memberships which have ended.
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='person')
    start = models.DateTimeField(_("start date"), default=timezone.now)
    end = models.DateTimeField(_("end date"), null=True, blank=True)

    def __str__(self):
        return 'GroupMembership(id={}, group={}, user={}, start={}, end={})'.format(
            self.id,
            self.group,
            self.user,
            self.start,
            self.end)


class ExternalCardLoan(models.Model):
    """For when someone borrows an external card from Q."""
    external_card = models.ForeignKey(ExternalCard, on_delete=models.PROTECT)
    person = models.ForeignKey(Person, on_delete=models.PROTECT)
    start = models.DateField(default=timezone.now)
    end = models.DateField(null=True,
                           blank=True,
                           help_text='If empty, the person is currently borrowing the card.')

    DEPOSIT_CHOICES = (
        ('n', 'No'),
        ('n?', 'Probably not'),
        ('y?', 'Probably yes'),
        ('y', 'Most definitely')
    )
    deposit_made = models.CharField(max_length=4,
                                    choices=DEPOSIT_CHOICES,
                                    blank=True,
                                    help_text='Money deposit for the card.')
