# Generated by Django 3.2.16 on 2023-01-30 04:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sdfs', '0006_alter_sdfsdu_sdf'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sdfsdu',
            old_name='sdf',
            new_name='sdfId',
        ),
    ]