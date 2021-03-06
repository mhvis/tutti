# Generated by Django 3.0.8 on 2020-08-20 17:18

from django.db import migrations, models
import localflavor.generic.models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0005_auto_20200818_1236'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='key',
            options={'ordering': ('number',)},
        ),
        migrations.AddField(
            model_name='membershiprequest',
            name='seen',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='membershiprequest',
            name='date_of_birth',
            field=models.DateField(blank=True, help_text='dd-mm-yyyy', null=True),
        ),
        migrations.AlterField(
            model_name='membershiprequest',
            name='email',
            field=models.EmailField(max_length=150, verbose_name='email address'),
        ),
        migrations.AlterField(
            model_name='membershiprequest',
            name='field_of_study',
            field=models.CharField(blank=True, help_text='Leave empty if not applicable.', max_length=150),
        ),
        migrations.AlterField(
            model_name='membershiprequest',
            name='iban',
            field=localflavor.generic.models.IBANField(blank=True, help_text='Providing your IBAN bank account number helps our administration for arranging the contribution fee at a later moment. This form does not authorize us to do a bank charge.', include_countries=None, max_length=34, use_nordea_extensions=False, verbose_name='IBAN'),
        ),
        migrations.AlterField(
            model_name='membershiprequest',
            name='initials',
            field=models.CharField(blank=True, help_text='Initials of your first name(s) if you have multiple. In Dutch: voorletters.', max_length=30),
        ),
        migrations.AlterField(
            model_name='membershiprequest',
            name='instruments',
            field=models.CharField(max_length=150, verbose_name='instrument(s) or voice'),
        ),
        migrations.AlterField(
            model_name='membershiprequest',
            name='is_student',
            field=models.BooleanField(blank=True, help_text='At any university or high school.', null=True, verbose_name='student'),
        ),
        migrations.AlterField(
            model_name='membershiprequest',
            name='street',
            field=models.CharField(blank=True, max_length=150, verbose_name='street and house number'),
        ),
        migrations.AlterField(
            model_name='membershiprequest',
            name='sub_association',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('vokollage', 'Vokollage – choir'), ('ensuite', 'Ensuite – symphony orchestra'), ('auletes', 'Auletes – wind orchestra'), ('piano', 'Piano member – join association-wide activities and use our rehearsal rooms')], help_text='Which sub-associations are you interested in? If you are not interested in the orchestra and choir, select piano member. Leave empty if you are not (yet) sure.', max_length=31, verbose_name='sub-association'),
        ),
        migrations.AlterField(
            model_name='membershiprequest',
            name='tue_card_number',
            field=models.IntegerField(blank=True, help_text='If you have a TU/e campus card, fill in the number that is printed sideways, which is different from your student number or s-number. We will then make it possible for you to enter the cultural section in Luna using your campus card, during off-hours. During the day however the entrance is usually always open to anyone.', null=True, verbose_name='TU/e card number'),
        ),
    ]
