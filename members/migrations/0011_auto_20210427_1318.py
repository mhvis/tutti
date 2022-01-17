# Generated by Django 3.1.8 on 2021-04-27 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0010_auto_20200912_1259'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gsuiteaccount',
            options={'verbose_name': 'Google Workspace account'},
        ),
        migrations.AlterField(
            model_name='person',
            name='gsuite_accounts',
            field=models.ManyToManyField(blank=True, to='members.GSuiteAccount', verbose_name='Google Workspace accounts'),
        ),
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='first name'),
        ),
    ]