# Generated by Django 5.1.3 on 2025-05-13 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_remove_preprocessedimage_image_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedbackimage',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending Review'), ('reviewed', 'Reviewed')], default='reviewed', max_length=20),
        ),
    ]
