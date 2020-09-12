# Generated by Django 3.0.8 on 2020-09-11 19:52

import uuid

from django.db import migrations, models


# Add unique field in 3 parts
# From: https://docs.djangoproject.com/en/3.1/howto/writing-migrations/#migrations-that-add-unique-fields

class Migration(migrations.Migration):
    dependencies = [
        ('members', '0006_auto_20200820_1918'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='azure_immutable_id',
            field=models.CharField(default=uuid.uuid4, editable=False, max_length=150, null=True),
        ),
    ]
