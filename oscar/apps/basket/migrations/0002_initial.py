# Generated by Django 3.2.16 on 2023-01-17 08:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalogue', '0001_initial'),
        ('basket', '0001_initial'),
        ('partner', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lineattribute',
            name='option',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogue.option', verbose_name='Option'),
        ),
        migrations.AddField(
            model_name='line',
            name='basket',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='basket.basket', verbose_name='Basket'),
        ),
        migrations.AddField(
            model_name='line',
            name='sdu',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='basket_lines', to='catalogue.sdu', verbose_name='Sdu'),
        ),
        migrations.AddField(
            model_name='line',
            name='stockrecord',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='basket_lines', to='partner.stockrecord'),
        ),
        migrations.AddField(
            model_name='basket',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='baskets', to=settings.AUTH_USER_MODEL, verbose_name='Owner'),
        ),
    ]
