from django.db import models
from members.models import QGroup, Person
from django.utils import timezone
from datetime import datetime
import pytz

utc=pytz.UTC


class Activity(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, default='n/a')
    hide_activity = models.BooleanField(default=False)
    hide_participants = models.BooleanField(default=False)
    cost = models.CharField(max_length=150, default='n/a')
    location = models.CharField(max_length=150, default='n/a')
    start_date = models.DateTimeField(null=True,
                                      blank=True,
                                      verbose_name='Start date')
    end_date = models.DateTimeField(null=True,
                                    blank=True,
                                    verbose_name='End date')
    closing_date = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name='Closing date')
    groups = models.ManyToManyField(QGroup,
                                    blank=True,
                                    verbose_name='Linked groups')
    participants = models.ManyToManyField(Person,
                                          blank=True,
                                          related_name='participants',
                                          verbose_name='Participants')
    owners = models.ManyToManyField(Person,
                                    blank=True,
                                    related_name='owners',
                                    verbose_name='Activity owners')

    class Meta:
        verbose_name = 'activity'
        verbose_name_plural = 'activities'

    @property
    def is_closed(self):
        return timezone.now() > self.closing_date or timezone.now() > self.start_date or timezone.now() > self.end_date
