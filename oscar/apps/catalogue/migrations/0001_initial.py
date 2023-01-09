# Generated by Django 3.2.16 on 2023-01-08 05:05

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import oscar.core.validators
import oscar.models.fields
import oscar.models.fields.autoslugfield
import oscar.models.fields.slugfield
import oscar.utils.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option', models.CharField(max_length=255, verbose_name='Option')),
            ],
            options={
                'verbose_name': 'Attribute option',
                'verbose_name_plural': 'Attribute options',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AttributeOptionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Attribute option group',
                'verbose_name_plural': 'Attribute option groups',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=255, unique=True)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('name', models.CharField(db_index=True, max_length=255, verbose_name='Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('meta_title', models.CharField(blank=True, max_length=255, null=True, verbose_name='Meta title')),
                ('meta_description', models.TextField(blank=True, null=True, verbose_name='Meta description')),
                ('image', models.ImageField(blank=True, max_length=255, null=True, upload_to='categories', verbose_name='Image')),
                ('slug', oscar.models.fields.slugfield.SlugField(max_length=255, verbose_name='Slug')),
                ('is_public', models.BooleanField(db_index=True, default=True, help_text='Show this category in search results and catalogue listings.', verbose_name='Is public')),
                ('ancestors_are_public', models.BooleanField(db_index=True, default=True, help_text='The ancestors of this category are public', verbose_name='Ancestor categories are public')),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'ordering': ['path'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=128, verbose_name='Name')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(blank=True, editable=False, max_length=128, populate_from='name', unique=True, verbose_name='Code')),
                ('type', models.CharField(choices=[('text', 'Text'), ('integer', 'Integer'), ('boolean', 'True / False'), ('float', 'Float'), ('date', 'Date'), ('select', 'Select'), ('radio', 'Radio'), ('multi_select', 'Multi select'), ('checkbox', 'Checkbox')], default='text', max_length=255, verbose_name='Type')),
                ('required', models.BooleanField(default=False, verbose_name='Is this option required?')),
                ('help_text', models.CharField(blank=True, help_text='Help text shown to the user on the add to basket form', max_length=255, null=True, verbose_name='Help text')),
                ('order', models.IntegerField(blank=True, db_index=True, help_text='Controls the ordering of sdu options on sdu detail pages', null=True, verbose_name='Ordering')),
                ('option_group', models.ForeignKey(blank=True, help_text='Select an option group if using type "Option" or "Multi Option"', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sdu_options', to='catalogue.attributeoptiongroup', verbose_name='Option Group')),
            ],
            options={
                'verbose_name': 'Option',
                'verbose_name_plural': 'Options',
                'ordering': ['order', 'name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Sdu',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('structure', models.CharField(choices=[('standalone', 'Stand-alone sdu'), ('parent', 'Parent sdu'), ('child', 'Child sdu')], default='standalone', max_length=10, verbose_name='Sdu structure')),
                ('is_public', models.BooleanField(db_index=True, default=True, help_text='Show this sdu in search results and catalogue listings.', verbose_name='Is public')),
                ('upc', oscar.models.fields.NullCharField(help_text='Universal Sdu Code (UPC) is an identifier for a sdu which is not specific to a particular  supplier. Eg an ISBN for a book.', max_length=64, unique=True, verbose_name='UPC')),
                ('title', models.CharField(blank=True, max_length=255, verbose_name='Title')),
                ('slug', oscar.models.fields.slugfield.SlugField(max_length=255, verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('meta_title', models.CharField(blank=True, max_length=255, null=True, verbose_name='Meta title')),
                ('meta_description', models.TextField(blank=True, null=True, verbose_name='Meta description')),
                ('rating', models.FloatField(editable=False, null=True, verbose_name='Rating')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date created')),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Date updated')),
                ('is_discountable', models.BooleanField(default=True, help_text='This flag indicates if this sdu can be used in an offer or not', verbose_name='Is discountable?')),
            ],
            options={
                'verbose_name': 'Sdu',
                'verbose_name_plural': 'Sdus',
                'ordering': ['-date_created'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SduAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('code', models.SlugField(max_length=128, validators=[django.core.validators.RegexValidator(message="Code can only contain the letters a-z, A-Z, digits, and underscores, and can't start with a digit.", regex='^[a-zA-Z_][0-9a-zA-Z_]*$'), oscar.core.validators.non_python_keyword], verbose_name='Code')),
                ('type', models.CharField(choices=[('text', 'Text'), ('integer', 'Integer'), ('boolean', 'True / False'), ('float', 'Float'), ('richtext', 'Rich Text'), ('date', 'Date'), ('datetime', 'Datetime'), ('option', 'Option'), ('multi_option', 'Multi Option'), ('entity', 'Entity'), ('file', 'File'), ('image', 'Image')], default='text', max_length=20, verbose_name='Type')),
                ('required', models.BooleanField(default=False, verbose_name='Required')),
                ('option_group', models.ForeignKey(blank=True, help_text='Select an option group if using type "Option" or "Multi Option"', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sdu_attributes', to='catalogue.attributeoptiongroup', verbose_name='Option Group')),
            ],
            options={
                'verbose_name': 'Sdu attribute',
                'verbose_name_plural': 'Sdu attributes',
                'ordering': ['code'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SduRecommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ranking', models.PositiveSmallIntegerField(db_index=True, default=0, help_text='Determines order of the sdus. A sdu with a higher value will appear before one with a lower ranking.', verbose_name='Ranking')),
                ('primary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='primary_recommendations', to='catalogue.sdu', verbose_name='Primary sdu')),
                ('recommendation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogue.sdu', verbose_name='Recommended sdu')),
            ],
            options={
                'verbose_name': 'Sdu recommendation',
                'verbose_name_plural': 'Sdu recomendations',
                'ordering': ['primary', '-ranking'],
                'abstract': False,
                'unique_together': {('primary', 'recommendation')},
            },
        ),
        migrations.CreateModel(
            name='SduImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original', models.ImageField(max_length=255, upload_to=oscar.utils.models.get_image_upload_path, verbose_name='Original')),
                ('caption', models.CharField(blank=True, max_length=200, verbose_name='Caption')),
                ('display_order', models.PositiveIntegerField(db_index=True, default=0, help_text='An image with a display order of zero will be the primary image for a sdu', verbose_name='Display order')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('sdu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='catalogue.sdu', verbose_name='Sdu')),
            ],
            options={
                'verbose_name': 'Sdu image',
                'verbose_name_plural': 'Sdu images',
                'ordering': ['display_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SduClass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(blank=True, editable=False, max_length=128, populate_from='name', unique=True, verbose_name='Slug')),
                ('requires_shipping', models.BooleanField(default=True, verbose_name='Requires shipping?')),
                ('track_stock', models.BooleanField(default=True, verbose_name='Track stock levels?')),
                ('options', models.ManyToManyField(blank=True, to='catalogue.Option', verbose_name='Options')),
            ],
            options={
                'verbose_name': 'Sdu class',
                'verbose_name_plural': 'Sdu classes',
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SduCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogue.category', verbose_name='Category')),
                ('sdu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogue.sdu', verbose_name='Sdu')),
            ],
            options={
                'verbose_name': 'Sdu category',
                'verbose_name_plural': 'Sdu categories',
                'ordering': ['sdu', 'category'],
                'abstract': False,
                'unique_together': {('sdu', 'category')},
            },
        ),
        migrations.CreateModel(
            name='SduAttributeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value_text', models.TextField(blank=True, null=True, verbose_name='Text')),
                ('value_integer', models.IntegerField(blank=True, db_index=True, null=True, verbose_name='Integer')),
                ('value_boolean', models.BooleanField(blank=True, db_index=True, null=True, verbose_name='Boolean')),
                ('value_float', models.FloatField(blank=True, db_index=True, null=True, verbose_name='Float')),
                ('value_richtext', models.TextField(blank=True, null=True, verbose_name='Richtext')),
                ('value_date', models.DateField(blank=True, db_index=True, null=True, verbose_name='Date')),
                ('value_datetime', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='DateTime')),
                ('value_file', models.FileField(blank=True, max_length=255, null=True, upload_to=oscar.utils.models.get_image_upload_path)),
                ('value_image', models.ImageField(blank=True, max_length=255, null=True, upload_to=oscar.utils.models.get_image_upload_path)),
                ('entity_object_id', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogue.sduattribute', verbose_name='Attribute')),
                ('entity_content_type', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('sdu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attribute_values', to='catalogue.sdu', verbose_name='Sdu')),
                ('value_multi_option', models.ManyToManyField(blank=True, related_name='multi_valued_attribute_values', to='catalogue.AttributeOption', verbose_name='Value multi option')),
                ('value_option', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogue.attributeoption', verbose_name='Value option')),
            ],
            options={
                'verbose_name': 'Sdu attribute value',
                'verbose_name_plural': 'Sdu attribute values',
                'abstract': False,
                'unique_together': {('attribute', 'sdu')},
            },
        ),
        migrations.AddField(
            model_name='sduattribute',
            name='sdu_class',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='catalogue.sduclass', verbose_name='Sdu type'),
        ),
        migrations.AddField(
            model_name='sdu',
            name='attributes',
            field=models.ManyToManyField(help_text='A sdu attribute is something that this sdu may have, such as a size, as specified by its class', through='catalogue.SduAttributeValue', to='catalogue.SduAttribute', verbose_name='Attributes'),
        ),
        migrations.AddField(
            model_name='sdu',
            name='categories',
            field=models.ManyToManyField(through='catalogue.SduCategory', to='catalogue.Category', verbose_name='Categories'),
        ),
        migrations.AddField(
            model_name='sdu',
            name='parent',
            field=models.ForeignKey(blank=True, help_text="Only choose a parent sdu if you're creating a child sdu.  For example if this is a size 4 of a particular t-shirt.  Leave blank if this is a stand-alone sdu (i.e. there is only one version of this sdu).", null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='catalogue.sdu', verbose_name='Parent sdu'),
        ),
        migrations.AddField(
            model_name='sdu',
            name='recommended_sdus',
            field=models.ManyToManyField(blank=True, help_text='These are sdus that are recommended to accompany the main sdu.', through='catalogue.SduRecommendation', to='catalogue.Sdu', verbose_name='Recommended sdus'),
        ),
        migrations.AddField(
            model_name='sdu',
            name='sdu_class',
            field=models.ForeignKey(blank=True, help_text='Choose what type of sdu this is', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='sdus', to='catalogue.sduclass', verbose_name='Sdu type'),
        ),
        migrations.AddField(
            model_name='sdu',
            name='sdu_options',
            field=models.ManyToManyField(blank=True, help_text="Options are values that can be associated with a item when it is added to a customer's basket.  This could be something like a personalised message to be printed on a T-shirt.", to='catalogue.Option', verbose_name='Sdu options'),
        ),
        migrations.AddField(
            model_name='attributeoption',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='catalogue.attributeoptiongroup', verbose_name='Group'),
        ),
        migrations.AlterUniqueTogether(
            name='sduattribute',
            unique_together={('code', 'sdu_class')},
        ),
        migrations.AlterUniqueTogether(
            name='attributeoption',
            unique_together={('group', 'option')},
        ),
    ]