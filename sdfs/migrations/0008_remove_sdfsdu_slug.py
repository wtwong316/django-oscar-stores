# Generated by Django 3.2.16 on 2023-01-30 06:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sdfs', '0007_rename_sdf_sdfsdu_sdfid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sdfsdu',
            name='slug',
        ),
    ]
