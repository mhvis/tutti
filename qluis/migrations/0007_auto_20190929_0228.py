# Generated by Django 2.2.5 on 2019-09-29 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qluis', '0006_auto_20190929_0224'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalcard',
            name='reference_number',
            field=models.IntegerField(null=True),
        ),
    ]
