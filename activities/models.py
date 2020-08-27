from django.db import models
from members.models import QGroup, Person
from django.utils import timezone


class Activity(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    hide_activity = models.BooleanField(default=False)
    hide_participants = models.BooleanField(default=False,
                                            help_text="Participants will be hidden for everyone except the organizers.")
    cost = models.DecimalField(max_digits=8,
                               decimal_places=2,
                               help_text="Used for display only, can't be used to automatically debit people "
                                         "using Q-rekening (as of yet).",
                               null=True,
                               blank=True)
    location = models.CharField(max_length=150, blank=True)
    start_date = models.DateTimeField(help_text="Start time and date of the activity.")
    end_date = models.DateTimeField(null=True, blank=True, help_text="End time and date of the activity.")
    closing_date = models.DateTimeField(null=True,
                                        blank=True,
                                        help_text="Time and date enlisting closes.")
    groups = models.ManyToManyField(QGroup,
                                    blank=True,
                                    verbose_name='linked groups',
                                    help_text="You can restrict sign up to people from certain groups. "
                                              "If you don't specify a group, all (current) members can sign up.")
    participants = models.ManyToManyField(Person,
                                          blank=True,
                                          related_name='activity_set')
    owners = models.ManyToManyField(Person,
                                    blank=True,
                                    related_name='activity_organized_set',
                                    verbose_name='organizers',
                                    help_text="Organizers can modify the activity and get participant contact details.")

    class Meta:
        verbose_name_plural = 'activities'

    @property
    def is_closed(self):
        if self.closing_date:
            return timezone.now() > self.closing_date
        else:
            return timezone.now() > self.start_date
