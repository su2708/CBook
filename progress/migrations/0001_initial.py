# Generated by Django 4.2 on 2025-01-19 16:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('testplans', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgressStatus',
            fields=[
                ('status_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('progress_status', models.CharField(max_length=50)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('plan_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress', to='testplans.testplan')),
            ],
        ),
    ]
