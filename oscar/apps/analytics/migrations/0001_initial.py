# Generated by Django 3.2.16 on 2023-01-17 08:48

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_views', models.PositiveIntegerField(default=0, verbose_name='Views')),
                ('num_basket_additions', models.PositiveIntegerField(default=0, verbose_name='Basket Additions')),
                ('num_purchases', models.PositiveIntegerField(db_index=True, default=0, verbose_name='Purchases')),
                ('score', models.FloatField(default=0.0, verbose_name='Score')),
            ],
            options={
                'verbose_name': 'Product record',
                'verbose_name_plural': 'Product records',
                'ordering': ['-num_purchases'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_product_views', models.PositiveIntegerField(default=0, verbose_name='Product Views')),
                ('num_basket_additions', models.PositiveIntegerField(default=0, verbose_name='Basket Additions')),
                ('num_inquiries', models.PositiveIntegerField(db_index=True, default=0, verbose_name='Inquirys')),
                ('num_inquiry_lines', models.PositiveIntegerField(db_index=True, default=0, verbose_name='Inquiry Lines')),
                ('num_inquiry_items', models.PositiveIntegerField(db_index=True, default=0, verbose_name='Inquiry Items')),
                ('total_spent', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12, verbose_name='Total Spent')),
                ('date_last_inquiry', models.DateTimeField(blank=True, null=True, verbose_name='Last Inquiry Date')),
            ],
            options={
                'verbose_name': 'User record',
                'verbose_name_plural': 'User records',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserProductView',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
            ],
            options={
                'verbose_name': 'User product view',
                'verbose_name_plural': 'User product views',
                'ordering': ['-pk'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserSearch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query', models.CharField(db_index=True, max_length=255, verbose_name='Search term')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'User search query',
                'verbose_name_plural': 'User search queries',
                'ordering': ['-pk'],
                'abstract': False,
            },
        ),
    ]
