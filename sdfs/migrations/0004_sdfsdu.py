# Generated by Django 3.2.16 on 2023-01-24 04:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sdfs', '0003_auto_20230119_0537'),
    ]

    operations = [
        migrations.CreateModel(
            name='SdfSdu',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Name')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='Slug')),
                ('size', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, null=True, verbose_name='Size in sqft')),
                ('household_size', models.IntegerField(default=1, verbose_name='Household size')),
                ('rent', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, null=True, verbose_name='Rent')),
                ('has_contract', models.BooleanField(default=False, verbose_name='Has contract')),
                ('has_individual_kitchen', models.BooleanField(default=False, verbose_name='Has individual kitchen')),
                ('has_individual_bath', models.BooleanField(default=False, verbose_name='Has individual bath')),
                ('has_exterior_window', models.BooleanField(default=False, verbose_name='Has exterior windows')),
                ('internal_grading', models.IntegerField(default=0, verbose_name='Internal grading')),
                ('sdf', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='Sdf', to='sdfs.sdfsdu', verbose_name='SdfSdu')),
            ],
            options={
                'verbose_name': 'Sdf sdu record',
                'verbose_name_plural': 'Sdf sdu records',
                'abstract': False,
            },
        ),
    ]