# Generated by Django 2.2.5 on 2019-09-29 02:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qluis', '0005_auto_20190929_0212'),
    ]

    operations = [
        migrations.RenameField(
            model_name='externalcard',
            old_name='number',
            new_name='reference_number',
        ),
        migrations.AddField(
            model_name='externalcard',
            name='card_number',
            field=models.IntegerField(default=None, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='group',
            name='description',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
    ]
