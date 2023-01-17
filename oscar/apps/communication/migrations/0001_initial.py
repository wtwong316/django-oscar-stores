# Generated by Django 3.2.16 on 2023-01-17 08:48

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import oscar.models.fields.autoslugfield


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunicationEventType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(blank=True, editable=False, help_text='Code used for looking up this event programmatically', max_length=128, populate_from='name', separator='_', unique=True, validators=[django.core.validators.RegexValidator(message="Code can only contain the uppercase letters (A-Z), digits, and underscores, and can't start with a digit.", regex='^[A-Z_][0-9A-Z_]*$')], verbose_name='Code')),
                ('name', models.CharField(db_index=True, max_length=255, verbose_name='Name')),
                ('category', models.CharField(choices=[('Order related', 'Order related'), ('User related', 'User related')], default='Order related', max_length=255, verbose_name='Category')),
                ('email_subject_template', models.CharField(blank=True, max_length=255, null=True, verbose_name='Email Subject Template')),
                ('email_body_template', models.TextField(blank=True, null=True, verbose_name='Email Body Template')),
                ('email_body_html_template', models.TextField(blank=True, help_text='HTML template', null=True, verbose_name='Email Body HTML Template')),
                ('sms_template', models.CharField(blank=True, help_text='SMS template', max_length=170, null=True, verbose_name='SMS Template')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Date Updated')),
            ],
            options={
                'verbose_name': 'Communication event type',
                'verbose_name_plural': 'Communication event types',
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('location', models.CharField(choices=[('Inbox', 'Inbox'), ('Archive', 'Archive')], default='Inbox', max_length=32)),
                ('date_sent', models.DateTimeField(auto_now_add=True)),
                ('date_read', models.DateTimeField(blank=True, null=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'ordering': ('-date_sent',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email Address')),
                ('subject', models.TextField(max_length=255, verbose_name='Subject')),
                ('body_text', models.TextField(verbose_name='Body Text')),
                ('body_html', models.TextField(blank=True, verbose_name='Body HTML')),
                ('date_sent', models.DateTimeField(auto_now_add=True, verbose_name='Date Sent')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='emails', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Email',
                'verbose_name_plural': 'Emails',
                'ordering': ['-date_sent'],
                'abstract': False,
            },
        ),
    ]
