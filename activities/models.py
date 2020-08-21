from django.db import models
from members.models import QGroup, Person


class Activity(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    date = models.DateField(null=True,
                            blank=True,
                            verbose_name='Date')
    closing_date = models.DateField(null=True,
                                    blank=True,
                                    verbose_name='Closing date')
    groups = models.ManyToManyField(QGroup,
                                    blank=True,
                                    verbose_name='Linked groups')
    participants = models.ManyToManyField(Person,
                                          blank=True,
                                          verbose_name='Participants')

    class Meta:
        verbose_name = 'activity'
        verbose_name_plural = 'activities'
