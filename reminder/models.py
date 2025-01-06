from django.db import models

class MessageStyle(models.TextChoices):
    GENTLE = 'GENTLE', '상냥한'
    STRICT = 'STRICT', '팩폭'
    FORMAL = 'FORMAL', '딱딱한'
    FUN = 'FUN', '재미있는'

class ReminderSettings(models.Model):
    class ReminderInterval(models.TextChoices):
        NONE = 'NONE', '알림 없음'
        HOURLY_1 = 'HOURLY_1', '1시간 마다'
        HOURLY_2 = 'HOURLY_2', '2시간 마다'
        HOURLY_3 = 'HOURLY_3', '3시간 마다'
    
    test_plan = models.OneToOneField(
        'testplans.TestPlan',
        on_delete=models.CASCADE,
        related_name='reminder_settings'
    )
    study_start_time = models.TimeField('학습 시작 시간', default='09:00')
    reminder_interval = models.CharField(
        max_length=10,
        choices=ReminderInterval.choices,
        default=ReminderInterval.NONE
    )
    message_style = models.CharField(
        max_length=10,
        choices=MessageStyle.choices,
        default=MessageStyle.GENTLE
    )
    created_at = models.DateTimeField(auto_now_add=True)

class ReminderTemplate(models.Model):
    message = models.TextField()
    message_style = models.CharField(
        max_length=10,
        choices=MessageStyle.choices
    )
    created_at = models.DateTimeField(auto_now_add=True)
