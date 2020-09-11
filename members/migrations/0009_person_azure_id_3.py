# Generated by Django 3.0.8 on 2020-09-11 19:52
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0008_person_azure_id_2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='azure_immutable_id',
            field=models.CharField(default=uuid.uuid4, editable=False, max_length=150, unique=True),
        ),
    ]