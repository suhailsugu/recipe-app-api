# Generated by Django 5.0.6 on 2024-07-08 08:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_recipe'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipe',
            old_name='desctiption',
            new_name='description',
        ),
    ]
