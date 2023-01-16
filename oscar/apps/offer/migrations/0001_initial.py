# Generated by Django 3.2.16 on 2023-01-16 07:31

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import oscar.models.fields
import oscar.models.fields.autoslugfield


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalogue', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Benefit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(blank=True, choices=[('Percentage', "Discount is a percentage off of the sdu's value"), ('Absolute', "Discount is a fixed amount off of the sdu's value"), ('Multibuy', 'Discount is to give the cheapest sdu for free'), ('Fixed price', 'Get the sdus that meet the condition for a fixed price'), ('Shipping absolute', 'Discount is a fixed amount of the shipping cost'), ('Shipping fixed price', 'Get shipping for a fixed price'), ('Shipping percentage', 'Discount is a percentage off of the shipping cost')], max_length=128, verbose_name='Type')),
                ('value', oscar.models.fields.PositiveDecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Value')),
                ('max_affected_items', models.PositiveIntegerField(blank=True, help_text='Set this to prevent the discount consuming all items within the range that are in the basket.', null=True, verbose_name='Max Affected Items')),
                ('proxy_class', oscar.models.fields.NullCharField(default=None, max_length=255, verbose_name='Custom class')),
            ],
            options={
                'verbose_name': 'Benefit',
                'verbose_name_plural': 'Benefits',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(blank=True, choices=[('Count', 'Depends on number of items in basket that are in condition range'), ('Value', 'Depends on value of items in basket that are in condition range'), ('Coverage', 'Needs to contain a set number of DISTINCT items from the condition range')], max_length=128, verbose_name='Type')),
                ('value', oscar.models.fields.PositiveDecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Value')),
                ('proxy_class', oscar.models.fields.NullCharField(default=None, max_length=255, verbose_name='Custom class')),
            ],
            options={
                'verbose_name': 'Condition',
                'verbose_name_plural': 'Conditions',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Range',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True, verbose_name='Name')),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(blank=True, editable=False, max_length=128, populate_from='name', unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False, help_text='Public ranges have a renter-facing page', verbose_name='Is public?')),
                ('includes_all_sdus', models.BooleanField(default=False, verbose_name='Includes all sdus?')),
                ('proxy_class', oscar.models.fields.NullCharField(default=None, max_length=255, unique=True, verbose_name='Custom class')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('classes', models.ManyToManyField(blank=True, related_name='classes', to='catalogue.SduClass', verbose_name='Sdu Types')),
                ('excluded_sdus', models.ManyToManyField(blank=True, related_name='excludes', to='catalogue.Sdu', verbose_name='Excluded Sdus')),
                ('included_categories', models.ManyToManyField(blank=True, related_name='includes', to='catalogue.Category', verbose_name='Included Categories')),
            ],
            options={
                'verbose_name': 'Range',
                'verbose_name_plural': 'Ranges',
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RangeSduFileUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filepath', models.CharField(max_length=255, verbose_name='File Path')),
                ('size', models.PositiveIntegerField(verbose_name='Size')),
                ('date_uploaded', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date Uploaded')),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Failed', 'Failed'), ('Processed', 'Processed')], default='Pending', max_length=32, verbose_name='Status')),
                ('error_message', models.CharField(blank=True, max_length=255, verbose_name='Error Message')),
                ('date_processed', models.DateTimeField(null=True, verbose_name='Date Processed')),
                ('num_new_skus', models.PositiveIntegerField(null=True, verbose_name='Number of New SKUs')),
                ('num_unknown_skus', models.PositiveIntegerField(null=True, verbose_name='Number of Unknown SKUs')),
                ('num_duplicate_skus', models.PositiveIntegerField(null=True, verbose_name='Number of Duplicate SKUs')),
                ('range', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='file_uploads', to='offer.range', verbose_name='Range')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Uploaded By')),
            ],
            options={
                'verbose_name': 'Range Sdu Uploaded File',
                'verbose_name_plural': 'Range Sdu Uploaded Files',
                'ordering': ('-date_uploaded',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RangeSdu',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_order', models.IntegerField(default=0)),
                ('range', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='offer.range')),
                ('sdu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogue.sdu')),
            ],
            options={
                'abstract': False,
                'unique_together': {('range', 'sdu')},
            },
        ),
        migrations.AddField(
            model_name='range',
            name='included_sdus',
            field=models.ManyToManyField(blank=True, related_name='includes', through='offer.RangeSdu', to='catalogue.Sdu', verbose_name='Included Sdus'),
        ),
        migrations.CreateModel(
            name='ConditionalOffer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="This is displayed within the renter's basket", max_length=128, unique=True, verbose_name='Name')),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(blank=True, editable=False, max_length=128, populate_from='name', unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, help_text='This is displayed on the offer browsing page', verbose_name='Description')),
                ('offer_type', models.CharField(choices=[('Site', 'Site offer - available to all users'), ('Voucher', 'Voucher offer - only available after entering the appropriate voucher code'), ('User', 'User offer - available to certain types of user'), ('Session', 'Session offer - temporary offer, available for a user for the duration of their session')], default='Site', max_length=128, verbose_name='Type')),
                ('exclusive', models.BooleanField(default=True, help_text='Exclusive offers cannot be combined on the same items', verbose_name='Exclusive offer')),
                ('status', models.CharField(default='Open', max_length=64, verbose_name='Status')),
                ('priority', models.IntegerField(db_index=True, default=0, help_text='The highest priority offers are applied first', verbose_name='Priority')),
                ('start_datetime', models.DateTimeField(blank=True, help_text='Offers are active from the start date. Leave this empty if the offer has no start date.', null=True, verbose_name='Start date')),
                ('end_datetime', models.DateTimeField(blank=True, help_text='Offers are active until the end date. Leave this empty if the offer has no expiry date.', null=True, verbose_name='End date')),
                ('max_global_applications', models.PositiveIntegerField(blank=True, help_text='The number of times this offer can be used before it is unavailable', null=True, verbose_name='Max global applications')),
                ('max_user_applications', models.PositiveIntegerField(blank=True, help_text='The number of times a single user can use this offer', null=True, verbose_name='Max user applications')),
                ('max_basket_applications', models.PositiveIntegerField(blank=True, help_text='The number of times this offer can be applied to a basket (and order)', null=True, verbose_name='Max basket applications')),
                ('max_discount', models.DecimalField(blank=True, decimal_places=2, help_text='When an offer has given more discount to orders than this threshold, then the offer becomes unavailable', max_digits=12, null=True, verbose_name='Max discount')),
                ('total_discount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12, verbose_name='Total Discount')),
                ('num_applications', models.PositiveIntegerField(default=0, verbose_name='Number of applications')),
                ('num_orders', models.PositiveIntegerField(default=0, verbose_name='Number of Orders')),
                ('redirect_url', oscar.models.fields.ExtendedURLField(blank=True, verbose_name='URL redirect (optional)')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('benefit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offers', to='offer.benefit', verbose_name='Benefit')),
                ('combinations', models.ManyToManyField(blank=True, help_text='Select other non-exclusive offers that this offer can be combined with on the same items', limit_choices_to={'exclusive': False}, related_name='in_combination', to='offer.ConditionalOffer')),
                ('condition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offers', to='offer.condition', verbose_name='Condition')),
            ],
            options={
                'verbose_name': 'Conditional offer',
                'verbose_name_plural': 'Conditional offers',
                'ordering': ['-priority', 'pk'],
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='condition',
            name='range',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='offer.range', verbose_name='Range'),
        ),
        migrations.AddField(
            model_name='benefit',
            name='range',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='offer.range', verbose_name='Range'),
        ),
        migrations.CreateModel(
            name='AbsoluteDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Absolute discount benefit',
                'verbose_name_plural': 'Absolute discount benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='CountCondition',
            fields=[
            ],
            options={
                'verbose_name': 'Count condition',
                'verbose_name_plural': 'Count conditions',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.condition',),
        ),
        migrations.CreateModel(
            name='CoverageCondition',
            fields=[
            ],
            options={
                'verbose_name': 'Coverage Condition',
                'verbose_name_plural': 'Coverage Conditions',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.condition',),
        ),
        migrations.CreateModel(
            name='FixedPriceBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Fixed price benefit',
                'verbose_name_plural': 'Fixed price benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='MultibuyDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Multibuy discount benefit',
                'verbose_name_plural': 'Multibuy discount benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='PercentageDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Percentage discount benefit',
                'verbose_name_plural': 'Percentage discount benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='ShippingBenefit',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='ValueCondition',
            fields=[
            ],
            options={
                'verbose_name': 'Value condition',
                'verbose_name_plural': 'Value conditions',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.condition',),
        ),
        migrations.CreateModel(
            name='ShippingAbsoluteDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Shipping absolute discount benefit',
                'verbose_name_plural': 'Shipping absolute discount benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.shippingbenefit',),
        ),
        migrations.CreateModel(
            name='ShippingFixedPriceBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Fixed price shipping benefit',
                'verbose_name_plural': 'Fixed price shipping benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.shippingbenefit',),
        ),
        migrations.CreateModel(
            name='ShippingPercentageDiscountBenefit',
            fields=[
            ],
            options={
                'verbose_name': 'Shipping percentage discount benefit',
                'verbose_name_plural': 'Shipping percentage discount benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.shippingbenefit',),
        ),
    ]
