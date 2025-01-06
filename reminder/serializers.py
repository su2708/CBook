from rest_framework import serializers
from .models import ReminderSettings, ReminderTemplate

class ReminderTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReminderTemplate
        fields = '__all__'

class ReminderSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReminderSettings
        fields = '__all__'
