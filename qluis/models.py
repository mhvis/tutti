from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime


class User(AbstractUser):
    """A Django user, different from a Quadrivium person."""
    pass


class Instrument(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class Group(models.Model):
    """A Quadrivium group, like the board and commissions.

    This differs from the built-in Django group model which is not used for
    this app!
    """
    name = models.CharField(_('name'), max_length=150, unique=True)
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    def __str__(self):
        return self.name


class ExternalCard(models.Model):
    card_number = models.IntegerField(null=True)
    reference_number = models.IntegerField(null=True)
    description = models.CharField(max_length=150,
                                   help_text='Additional indication that is written on the card.',
                                   blank=True)

    def __str__(self):
        return '{} {} {}'.format(self.card_number,
                                 self.reference_number,
                                 self.description).strip()


class GSuiteAccount(models.Model):
    email = models.EmailField()

    def __str__(self):
        return self.email


class Key(models.Model):
    number = models.IntegerField(unique=True)
    room_name = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return '{} {}'.format(self.number, self.room_name).strip()


class Person(models.Model):
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), blank=True)

    # password = models.CharField(_('password'), max_length=128)
    initials = models.CharField(max_length=30, blank=True)
    street = models.CharField(max_length=150, blank=True)
    postal_code = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=150, blank=True)

    phone_number = PhoneNumberField(blank=True)

    PREFERRED_LANGUAGES = (
        ('en-us', 'English'),
        ('nl-nl', 'Dutch'),
    )
    preferred_language = models.CharField(max_length=30,
                                          blank=True,
                                          choices=PREFERRED_LANGUAGES)
    tue_card_number = models.IntegerField(null=True)
    date_of_birth = models.DateField(null=True)
    gender = models.CharField(max_length=30,
                              blank=True,
                              choices=(('male', 'Male'), ('female', 'Female')))
    is_student = models.BooleanField(null=True)
    membership_start = models.DateField(null=True)
    membership_end = models.DateField(null=True)
    permission_exquus = models.BooleanField(null=True)
    sepa_direct_debit = models.BooleanField(null=True)

    instruments = models.ManyToManyField(Instrument, blank=True)

    bhv_certificate = models.DateField(null=True)

    external_card = models.ForeignKey(ExternalCard,
                                      on_delete=models.SET_NULL,
                                      null=True)
    external_card_deposit_made = models.BooleanField(null=True)

    field_of_study = models.CharField(max_length=150,
                                      blank=True)

    found_via = models.CharField(max_length=30, blank=True)
    gsuite_accounts = models.ManyToManyField(GSuiteAccount, blank=True)

    iban = models.CharField(max_length=150, blank=True)
    person_id = models.CharField(max_length=30, blank=True)

    key_access = models.ManyToManyField(Key, blank=True)
    keywatcher_id = models.CharField(max_length=4, blank=True)
    keywatcher_pin = models.CharField(max_length=4, blank=True)

    # qMailbox is not used
    # qPermissionMedia is not used!

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to.'
        ),
    )

    created_at = models.DateTimeField(default=timezone.now)
    # created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
    #                                on_delete=models.SET_NULL,
    #                                null=True)

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = '{} {}'.format(self.first_name, self.last_name)
        return full_name.strip()

    def unsubscribe(self):
        self.membership_end = datetime.now()
        # Go over all groups

        self.save()

    def __str__(self):
        return self.get_full_name()
