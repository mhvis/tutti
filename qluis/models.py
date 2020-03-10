from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """A Django user, different from a Quadrivium person."""
    pass


class Instrument(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class QGroup(models.Model):
    """A Quadrivium group, like the board and commissions.

    It is named this way to prevent confusion with the Django built-in Group
    model.
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
    card_number = models.IntegerField(null=True,
                                      help_text="7-digit (usually) card identifier number.")
    reference_number = models.IntegerField(null=True,
                                           blank=True,
                                           help_text='Short reference number written on the card.')
    description = models.CharField(max_length=150,
                                   help_text='Additional indication that is written on the card.',
                                   blank=True)

    # loans =

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
    tue_card_number = models.IntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=30,
                              blank=True,
                              choices=(('male', 'Male'), ('female', 'Female')))
    is_student = models.BooleanField(null=True, blank=True)

    sepa_direct_debit = models.BooleanField(null=True, blank=True)

    instruments = models.ManyToManyField(Instrument, blank=True)

    bhv_certificate = models.DateField(null=True, blank=True)

    external_card = models.ForeignKey(ExternalCard,
                                      on_delete=models.SET_NULL,
                                      null=True,
                                      blank=True
                                      )
    external_card_deposit_made = models.BooleanField(null=True, blank=True)

    field_of_study = models.CharField(max_length=150,
                                      blank=True)

    gsuite_accounts = models.ManyToManyField(GSuiteAccount, blank=True)

    iban = models.CharField(max_length=150, blank=True, verbose_name='IBAN')
    person_id = models.CharField(max_length=30, blank=True)

    key_access = models.ManyToManyField(Key, blank=True)
    keywatcher_id = models.CharField(max_length=4,
                                     blank=True,
                                     verbose_name='KeyWatcher ID')
    keywatcher_pin = models.CharField(max_length=4,
                                      blank=True,
                                      verbose_name='KeyWatcher PIN')

    # qMailbox is not used
    # qPermissionMedia is not used!

    groups = models.ManyToManyField(
        QGroup,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to.'
        ),
        through='Membership'
    )

    created_at = models.DateTimeField(default=timezone.now)

    # created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
    #                                on_delete=models.SET_NULL,
    #                                null=True)

    notes = models.TextField(blank=True)

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = '{} {}'.format(self.first_name, self.last_name)
        return full_name.strip()

    def __str__(self):
        return self.get_full_name()


class Membership(models.Model):
    """Group membership.

    If end date is given, that means that the person is not a group member
    anymore.
    """

    class Meta:
        constraints = [
            # Allow only one membership instance per group/person combi
            models.UniqueConstraint(fields=['group', 'person'],
                                    name='unique_memberships',
                                    condition=Q(end=None))
        ]

    group = models.ForeignKey(QGroup, on_delete=models.PROTECT)
    person = models.ForeignKey(Person, on_delete=models.PROTECT)
    start = models.DateTimeField(_("start date"), default=timezone.now)
    end = models.DateTimeField(_("end date"), null=True, blank=True)

    def end_now(self):
        """End a group membership."""
        self.end = timezone.now()
        self.save()

# class ExternalCardLoan(models.Model):
#     DEPOSIT_CHOICES = (
#         (1, 'Probably not'),
#         (2, 'Probably yes'),
#         (3, 'Most definitely')
#     )
#     deposit_made = models.IntegerField(choices=DEPOSIT_CHOICES)
