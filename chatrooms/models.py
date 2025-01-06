from django.db import models
from django.conf import settings
from testplans.models import TestPlan

# Create your models here.
class ChatRoom(models.Model):
    chat_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chatrooms"
    )
    chat_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name