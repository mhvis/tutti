# Generated by Django 4.2.13 on 2024-09-08 15:59

from django.db import migrations, models
import members.models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0014_person_photo_video_consent_external_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='photo_video_consent_external_group',
            field=models.BooleanField(blank=True, help_text='Whether the person has given consent to share group photos and videos of them externally (on website, social media). With group is meant large groups, such as pictures of a full orchestra or choir during a concert.', null=True, verbose_name='photos/videos consent external group'),
        ),
        migrations.AlterField(
            model_name='person',
            name='photo_video_consent_external',
            field=models.BooleanField(blank=True, help_text='Whether the person has given consent to share other photos and videos of them externally (on website, social media).', null=True, verbose_name='photos/videos consent external non-group'),
        ),
        migrations.AlterField(
            model_name='person',
            name='photo_video_consent_internal',
            field=models.BooleanField(blank=True, help_text='Whether the person has given consent to share photos and videos of them internally with other members.', null=True, verbose_name='photos/videos consent internal'),
        )
    ]
