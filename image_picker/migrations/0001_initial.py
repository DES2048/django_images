# Generated by Django 3.1 on 2020-08-15 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('title', models.CharField(max_length=128)),
                ('slug', models.SlugField(max_length=128, primary_key=True, serialize=False)),
                ('dir_path', models.CharField(max_length=255, unique=True)),
            ],
        ),
    ]
