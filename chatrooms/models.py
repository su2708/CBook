from django.db import models
from django.conf import settings
from testplans.models import TestPlan

# Create your models here.
class ChatRoom(models.Model):
    chat_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chatrooms"
    )
    testplan = models.OneToOneField(
        TestPlan, on_delete=models.SET_NULL, related_name="chatroom", null=True, blank=True
    )
    chat_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.chat_name


class ChatMessage(models.Model):
    message_id = models.AutoField(primary_key=True)
    chat_id = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="chatmessages"
    )
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chatmessages"
    )
    message_content = models.JSONField()  # 메시지 본문 
    SENDER_CHOICES = [("user", "User"), ("ai", "AI")]  # 발신자를 user 또는 ai로 구분 
    sent_by = models.CharField(max_length=20, choices=SENDER_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"[{self.sent_at}] {self.sent_by}: {self.message_content}"