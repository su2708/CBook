from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

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
        related_name='reminder_settings',
        to_field='plan_id'
    )
    study_start_hour = models.IntegerField(
        '학습 시작 시간',
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        default=9
    )
    study_end_hour = models.IntegerField(
        '학습 종료 시간',
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        default=18
    )
    reminder_interval = models.CharField(
        '알림 간격',
        max_length=10,
        choices=ReminderInterval.choices,
        default=ReminderInterval.NONE
    )
    message_style = models.CharField(
        '메시지 스타일',
        max_length=10,
        choices=MessageStyle.choices,
        default=MessageStyle.GENTLE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.study_start_hour >= self.study_end_hour:
            raise ValidationError('학습 종료 시간은 시작 시간보다 늦어야 합니다.')

class ReminderMessage(models.Model):
    """Fixture 데이터로 관리될 메시지 템플릿"""
    message = models.TextField('메시지 내용')
    message_style = models.CharField(
        '메시지 스타일',
        max_length=10,
        choices=MessageStyle.choices
    )