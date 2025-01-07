from rest_framework import serializers
from .models import ReminderSettings, ReminderMessage

class ReminderMessageSerializer(serializers.ModelSerializer):
    message_style_display = serializers.CharField(source='get_message_style_display', read_only=True)
    
    class Meta:
        model = ReminderMessage
        fields = ['id', 'message', 'message_style', 'message_style_display']

class ReminderSettingsSerializer(serializers.ModelSerializer):
    reminder_interval_display = serializers.CharField(source='get_reminder_interval_display', read_only=True)
    message_style_display = serializers.CharField(source='get_message_style_display', read_only=True)
    
    class Meta:
        model = ReminderSettings
        fields = [
            'id', 
            'test_plan',
            'study_start_hour',
            'study_end_hour',
            'reminder_interval',
            'reminder_interval_display',
            'message_style',
            'message_style_display',
            'created_at'
        ]
        read_only_fields = ['created_at']

    def validate(self, data):
        """시작 시간이 종료 시간보다 늦을 수 없음"""
        if data.get('study_start_hour') >= data.get('study_end_hour'):
            raise serializers.ValidationError(
                "학습 종료 시간은 시작 시간보다 늦어야 합니다."
            )
        return data