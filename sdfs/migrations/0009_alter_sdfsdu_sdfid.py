# Generated by Django 3.2.16 on 2023-01-30 06:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sdfs', '0008_remove_sdfsdu_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sdfsdu',
            name='sdfId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Sdf', to='sdfs.sdf', verbose_name='SdfId'),
        ),
    ]