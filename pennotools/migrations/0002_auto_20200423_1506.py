# Generated by Django 3.0.5 on 2020-04-23 13:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pennotools', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='permissions',
            options={'default_permissions': (), 'managed': False, 'permissions': (('can_access', 'Can use the treasurer tools'),)},
        ),
    ]