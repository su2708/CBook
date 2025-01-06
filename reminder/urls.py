from django.urls import path
from .views import get_reminder_templates, reminder_settings, update_reminder_settings

urlpatterns = [
    path('templates/', get_reminder_templates, name='reminder-template-list'),  # 템플릿 조회
    path('settings/<int:plan_id>/', reminder_settings, name='reminder-settings'),  # 알림 설정 조회 및 생성
    path('settings/<int:plan_id>/update/', update_reminder_settings, name='reminder-settings-update'),  # 알림 설정 수정
]