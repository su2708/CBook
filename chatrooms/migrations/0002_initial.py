# Generated by Django 4.2 on 2025-01-18 02:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('testplans', '0001_initial'),
        ('chatrooms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroom',
            name='testplan',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='linked_chatroom', to='testplans.testplan'),
        ),
        migrations.AddField(
            model_name='chatroom',
            name='user_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chatrooms', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='chat_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chatmessages', to='chatrooms.chatroom'),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='user_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chatmessages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='chatroom',
            unique_together={('user_id', 'chat_id')},
        ),
        migrations.AlterUniqueTogether(
            name='chatmessage',
            unique_together={('message_id', 'chat_id')},
        ),
    ]
