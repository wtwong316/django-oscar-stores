# Generated by Django 3.2.16 on 2023-02-23 04:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sdfs', '0011_auto_20230221_0313'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sdfsdu',
            name='building',
            field=models.CharField(default='', max_length=25, null=True, verbose_name='大廈名稱'),
        ),
        migrations.AlterField(
            model_name='sdfsdu',
            name='district',
            field=models.CharField(default='', max_length=25, verbose_name='行政分區'),
        ),
        migrations.AlterField(
            model_name='sdfsdu',
            name='has_contract',
            field=models.BooleanField(default=False, verbose_name='有租约'),
        ),
        migrations.AlterField(
            model_name='sdfsdu',
            name='has_exterior_window',
            field=models.BooleanField(default=False, verbose_name='有外窗'),
        ),
        migrations.AlterField(
            model_name='sdfsdu',
            name='has_individual_bath',
            field=models.BooleanField(default=False, verbose_name='有獨立浴室'),
        ),
        migrations.AlterField(
            model_name='sdfsdu',
            name='has_individual_kitchen',
            field=models.BooleanField(default=False, verbose_name='有獨立廚房'),
        ),
        migrations.AlterField(
            model_name='sdfsdu',
            name='household_size',
            field=models.IntegerField(default=1, verbose_name='住户人数'),
        ),
        migrations.AlterField(
            model_name='sdfsdu',
            name='internal_grading',
            field=models.IntegerField(default=0, verbose_name='内部裝修评分'),
        ),
        migrations.AlterField(
            model_name='sdfsdu',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='有效'),
        ),
        migrations.AlterField(
            model_name='sdfsdu',
            name='name',
            field=models.CharField(max_length=25, unique=True, verbose_name='調查編號'),
        ),
        migrations.AlterField(
            model_name='sdfsdu',
            name='rent',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, null=True, verbose_name='每月租金'),
        ),
        migrations.AlterField(
            model_name='sdfsdu',
            name='size',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, null=True, verbose_name='面積（平方英尺)'),
        ),
    ]