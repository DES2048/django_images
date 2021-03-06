# Generated by Django 3.1 on 2020-08-22 13:03

from django.db import migrations, models
import image_picker.validators


class Migration(migrations.Migration):

    dependencies = [
        ('image_picker', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gallery',
            options={'verbose_name_plural': 'Galleries'},
        ),
        migrations.AlterField(
            model_name='gallery',
            name='dir_path',
            field=models.CharField(max_length=255, unique=True, validators=[image_picker.validators.validate_path_exists]),
        ),
    ]
