# Generated by Django 5.1.3 on 2025-01-19 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_feedbackimage_retrained'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], max_length=10)),
                ('message', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('module', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
    ]
