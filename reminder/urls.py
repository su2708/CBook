from django.urls import path
from .views import get_reminder_messages, reminder_settings, update_reminder_settings

app_name = 'reminders'

urlpatterns = [
    path('messages/', get_reminder_messages, name='reminder-message-list'),
    path('settings/<int:plan_id>/', reminder_settings, name='reminder-settings'),
    path('settings/<int:plan_id>/update/', update_reminder_settings, name='reminder-settings-update'),
]