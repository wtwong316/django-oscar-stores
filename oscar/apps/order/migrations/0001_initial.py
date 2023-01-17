# Generated by Django 3.2.16 on 2023-01-17 08:48

from django.conf import settings
import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
import oscar.core.utils
import oscar.models.fields
import oscar.models.fields.autoslugfield
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalogue', '0001_initial'),
        ('partner', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sites', '0002_alter_domain_unique'),
        ('address', '0001_initial'),
        ('communication', '0001_initial'),
        ('basket', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, choices=[('Mr', 'Mr'), ('Miss', 'Miss'), ('Mrs', 'Mrs'), ('Ms', 'Ms'), ('Dr', 'Dr')], max_length=64, verbose_name='Title')),
                ('first_name', models.CharField(blank=True, max_length=255, verbose_name='First name')),
                ('last_name', models.CharField(blank=True, max_length=255, verbose_name='Last name')),
                ('line1', models.CharField(max_length=255, verbose_name='First line of address')),
                ('line2', models.CharField(blank=True, max_length=255, verbose_name='Second line of address')),
                ('line3', models.CharField(blank=True, max_length=255, verbose_name='Third line of address')),
                ('line4', models.CharField(blank=True, max_length=255, verbose_name='City')),
                ('state', models.CharField(blank=True, max_length=255, verbose_name='State/County')),
                ('postcode', oscar.models.fields.UppercaseCharField(blank=True, max_length=64, verbose_name='Post/Zip-code')),
                ('search_text', models.TextField(editable=False, verbose_name='Search text - used only for searching addresses')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address.country', verbose_name='Country')),
            ],
            options={
                'verbose_name': 'Billing address',
                'verbose_name_plural': 'Billing addresses',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('partner_name', models.CharField(blank=True, max_length=128, verbose_name='Partner name')),
                ('partner_sku', models.CharField(max_length=128, verbose_name='Partner SKU')),
                ('partner_line_reference', models.CharField(blank=True, help_text='This is the item number that the partner uses within their system', max_length=128, verbose_name='Partner reference')),
                ('partner_line_notes', models.TextField(blank=True, verbose_name='Partner Notes')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('upc', models.CharField(blank=True, max_length=128, null=True, verbose_name='UPC')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Quantity')),
                ('line_price_incl_tax', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Price (inc. tax)')),
                ('line_price_excl_tax', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Price (excl. tax)')),
                ('line_price_before_discounts_incl_tax', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Price before discounts (inc. tax)')),
                ('line_price_before_discounts_excl_tax', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Price before discounts (excl. tax)')),
                ('unit_price_incl_tax', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Unit Price (inc. tax)')),
                ('unit_price_excl_tax', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Unit Price (excl. tax)')),
                ('status', models.CharField(blank=True, max_length=255, verbose_name='Status')),
            ],
            options={
                'verbose_name': 'Order Line',
                'verbose_name_plural': 'Order Lines',
                'ordering': ['pk'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(db_index=True, max_length=128, unique=True, verbose_name='Order number')),
                ('currency', models.CharField(default=oscar.core.utils.get_default_currency, max_length=12, verbose_name='Currency')),
                ('total_incl_tax', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Order total (inc. tax)')),
                ('total_excl_tax', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Order total (excl. tax)')),
                ('shipping_incl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Shipping charge (inc. tax)')),
                ('shipping_excl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Shipping charge (excl. tax)')),
                ('shipping_method', models.CharField(blank=True, max_length=128, verbose_name='Shipping method')),
                ('shipping_code', models.CharField(blank=True, default='', max_length=128)),
                ('status', models.CharField(blank=True, max_length=100, verbose_name='Status')),
                ('guest_email', models.EmailField(blank=True, max_length=254, verbose_name='Guest email address')),
                ('date_placed', models.DateTimeField(db_index=True)),
                ('basket', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='basket.basket', verbose_name='Basket')),
                ('billing_address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='order.billingaddress', verbose_name='Billing Address')),
            ],
            options={
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
                'ordering': ['-date_placed'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaymentEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Amount')),
                ('reference', models.CharField(blank=True, max_length=128, verbose_name='Reference')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date created')),
            ],
            options={
                'verbose_name': 'Payment Event',
                'verbose_name_plural': 'Payment Events',
                'ordering': ['-date_created'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaymentEventType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True, verbose_name='Name')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(blank=True, editable=False, max_length=128, populate_from='name', unique=True, verbose_name='Code')),
            ],
            options={
                'verbose_name': 'Payment Event Type',
                'verbose_name_plural': 'Payment Event Types',
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShippingEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True, help_text='This could be the dispatch reference, or a tracking number', verbose_name='Event notes')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date Created')),
            ],
            options={
                'verbose_name': 'Shipping Event',
                'verbose_name_plural': 'Shipping Events',
                'ordering': ['-date_created'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShippingEventType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Name')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(blank=True, editable=False, max_length=128, populate_from='name', unique=True, verbose_name='Code')),
            ],
            options={
                'verbose_name': 'Shipping Event Type',
                'verbose_name_plural': 'Shipping Event Types',
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Surcharge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Surcharge')),
                ('code', models.CharField(max_length=128, verbose_name='Surcharge code')),
                ('incl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Surcharge (inc. tax)')),
                ('excl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Surcharge (excl. tax)')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='surcharges', to='order.order', verbose_name='Surcharges')),
            ],
            options={
                'ordering': ['pk'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShippingEventQuantity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(verbose_name='Quantity')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='line_quantities', to='order.shippingevent', verbose_name='Event')),
                ('line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shipping_event_quantities', to='order.line', verbose_name='Line')),
            ],
            options={
                'verbose_name': 'Shipping Event Quantity',
                'verbose_name_plural': 'Shipping Event Quantities',
                'unique_together': {('event', 'line')},
            },
        ),
        migrations.AddField(
            model_name='shippingevent',
            name='event_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order.shippingeventtype', verbose_name='Event Type'),
        ),
        migrations.AddField(
            model_name='shippingevent',
            name='lines',
            field=models.ManyToManyField(related_name='shipping_events', through='order.ShippingEventQuantity', to='order.Line', verbose_name='Lines'),
        ),
        migrations.AddField(
            model_name='shippingevent',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shipping_events', to='order.order', verbose_name='Order'),
        ),
        migrations.CreateModel(
            name='ShippingAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, choices=[('Mr', 'Mr'), ('Miss', 'Miss'), ('Mrs', 'Mrs'), ('Ms', 'Ms'), ('Dr', 'Dr')], max_length=64, verbose_name='Title')),
                ('first_name', models.CharField(blank=True, max_length=255, verbose_name='First name')),
                ('last_name', models.CharField(blank=True, max_length=255, verbose_name='Last name')),
                ('line1', models.CharField(max_length=255, verbose_name='First line of address')),
                ('line2', models.CharField(blank=True, max_length=255, verbose_name='Second line of address')),
                ('line3', models.CharField(blank=True, max_length=255, verbose_name='Third line of address')),
                ('line4', models.CharField(blank=True, max_length=255, verbose_name='City')),
                ('state', models.CharField(blank=True, max_length=255, verbose_name='State/County')),
                ('postcode', oscar.models.fields.UppercaseCharField(blank=True, max_length=64, verbose_name='Post/Zip-code')),
                ('search_text', models.TextField(editable=False, verbose_name='Search text - used only for searching addresses')),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, help_text='In case we need to call you about your order', max_length=128, region=None, verbose_name='Phone number')),
                ('notes', models.TextField(blank=True, help_text='Tell us anything we should know when delivering your order.', verbose_name='Instructions')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address.country', verbose_name='Country')),
            ],
            options={
                'verbose_name': 'Shipping address',
                'verbose_name_plural': 'Shipping addresses',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaymentEventQuantity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(verbose_name='Quantity')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='line_quantities', to='order.paymentevent', verbose_name='Event')),
                ('line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_event_quantities', to='order.line', verbose_name='Line')),
            ],
            options={
                'verbose_name': 'Payment Event Quantity',
                'verbose_name_plural': 'Payment Event Quantities',
                'unique_together': {('event', 'line')},
            },
        ),
        migrations.AddField(
            model_name='paymentevent',
            name='event_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order.paymenteventtype', verbose_name='Event Type'),
        ),
        migrations.AddField(
            model_name='paymentevent',
            name='lines',
            field=models.ManyToManyField(through='order.PaymentEventQuantity', to='order.Line', verbose_name='Lines'),
        ),
        migrations.AddField(
            model_name='paymentevent',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_events', to='order.order', verbose_name='Order'),
        ),
        migrations.AddField(
            model_name='paymentevent',
            name='shipping_event',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payment_events', to='order.shippingevent'),
        ),
        migrations.CreateModel(
            name='OrderStatusChange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_status', models.CharField(blank=True, max_length=100, verbose_name='Old Status')),
                ('new_status', models.CharField(blank=True, max_length=100, verbose_name='New Status')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date Created')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_changes', to='order.order', verbose_name='Order Status Changes')),
            ],
            options={
                'verbose_name': 'Order Status Change',
                'verbose_name_plural': 'Order Status Changes',
                'ordering': ['-date_created'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrderNote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note_type', models.CharField(blank=True, max_length=128, verbose_name='Note Type')),
                ('message', models.TextField(verbose_name='Message')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Date Updated')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='order.order', verbose_name='Order')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Order Note',
                'verbose_name_plural': 'Order Notes',
                'ordering': ['-date_updated'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrderDiscount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('Basket', 'Basket'), ('Shipping', 'Shipping'), ('Deferred', 'Deferred')], default='Basket', max_length=64, verbose_name='Discount category')),
                ('offer_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='Offer ID')),
                ('offer_name', models.CharField(blank=True, db_index=True, max_length=128, verbose_name='Offer name')),
                ('voucher_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='Voucher ID')),
                ('voucher_code', models.CharField(blank=True, db_index=True, max_length=128, verbose_name='Code')),
                ('frequency', models.PositiveIntegerField(null=True, verbose_name='Frequency')),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Amount')),
                ('message', models.TextField(blank=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discounts', to='order.order', verbose_name='Order')),
            ],
            options={
                'verbose_name': 'Order Discount',
                'verbose_name_plural': 'Order Discounts',
                'ordering': ['pk'],
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='order.shippingaddress', verbose_name='Shipping Address'),
        ),
        migrations.AddField(
            model_name='order',
            name='site',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='sites.site', verbose_name='Site'),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.CreateModel(
            name='LinePrice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Quantity')),
                ('price_incl_tax', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Price (inc. tax)')),
                ('price_excl_tax', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Price (excl. tax)')),
                ('shipping_incl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Shiping (inc. tax)')),
                ('shipping_excl_tax', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Shipping (excl. tax)')),
                ('line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='order.line', verbose_name='Line')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='line_prices', to='order.order', verbose_name='Option')),
            ],
            options={
                'verbose_name': 'Line Price',
                'verbose_name_plural': 'Line Prices',
                'ordering': ('id',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LineAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=128, verbose_name='Type')),
                ('value', models.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder, verbose_name='Value')),
                ('line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='order.line', verbose_name='Line')),
                ('option', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='line_attributes', to='catalogue.option', verbose_name='Option')),
            ],
            options={
                'verbose_name': 'Line Attribute',
                'verbose_name_plural': 'Line Attributes',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='line',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='order.order', verbose_name='Order'),
        ),
        migrations.AddField(
            model_name='line',
            name='partner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_lines', to='partner.partner', verbose_name='Partner'),
        ),
        migrations.AddField(
            model_name='line',
            name='sdu',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalogue.sdu', verbose_name='Sdu'),
        ),
        migrations.AddField(
            model_name='line',
            name='stockrecord',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='partner.stockrecord', verbose_name='Stock record'),
        ),
        migrations.CreateModel(
            name='CommunicationEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date')),
                ('event_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='communication.communicationeventtype', verbose_name='Event Type')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='communication_events', to='order.order', verbose_name='Order')),
            ],
            options={
                'verbose_name': 'Communication Event',
                'verbose_name_plural': 'Communication Events',
                'ordering': ['-date_created'],
                'abstract': False,
            },
        ),
    ]
