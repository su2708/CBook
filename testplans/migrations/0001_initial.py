# Generated by Django 4.2 on 2025-01-16 17:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("chatrooms", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TestPlan",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("plan_id", models.IntegerField(blank=True, null=True)),
                ("test_name", models.CharField(max_length=50)),
                ("test_date", models.CharField(max_length=50)),
                ("test_place", models.CharField(max_length=200)),
                ("test_plan", models.JSONField(null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("on_progress", models.BooleanField(default=1)),
                (
                    "chatroom",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="linked_testplan",
                        to="chatrooms.chatroom",
                    ),
                ),
                (
                    "user_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="testplans",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("plan_id", "chatroom")},
            },
        ),
    ]
