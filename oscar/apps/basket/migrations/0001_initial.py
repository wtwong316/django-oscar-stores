# Generated by Django 3.2.16 on 2023-01-16 07:31

import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
import oscar.core.utils
import oscar.models.fields.slugfield


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Basket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Open', 'Open - currently active'), ('Merged', 'Merged - superceded by another basket'), ('Saved', 'Saved - for items to be purchased later'), ('Frozen', 'Frozen - the basket cannot be modified'), ('Submitted', 'Submitted - has been ordered at the checkout')], default='Open', max_length=128, verbose_name='Status')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_merged', models.DateTimeField(blank=True, null=True, verbose_name='Date merged')),
                ('date_submitted', models.DateTimeField(blank=True, null=True, verbose_name='Date submitted')),
            ],
            options={
                'verbose_name': 'Basket',
                'verbose_name_plural': 'Baskets',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line_reference', oscar.models.fields.slugfield.SlugField(max_length=128, verbose_name='Line Reference')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Quantity')),
                ('price_currency', models.CharField(default=oscar.core.utils.get_default_currency, max_length=12, verbose_name='Currency')),
                ('price_excl_tax', models.DecimalField(decimal_places=2, max_digits=12, null=True, verbose_name='Price excl. Tax')),
                ('price_incl_tax', models.DecimalField(decimal_places=2, max_digits=12, null=True, verbose_name='Price incl. Tax')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date Created')),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Date Updated')),
            ],
            options={
                'verbose_name': 'Basket line',
                'verbose_name_plural': 'Basket lines',
                'ordering': ['date_created', 'pk'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LineAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder, verbose_name='Value')),
                ('line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='basket.line', verbose_name='Line')),
            ],
            options={
                'verbose_name': 'Line attribute',
                'verbose_name_plural': 'Line attributes',
                'abstract': False,
            },
        ),
    ]
