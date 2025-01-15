from django.apps import AppConfig
from django.conf import settings

class ReminderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reminder'
    
    def ready(self):
        if settings.DEBUG:
            # Development 환경에서는 reloader로 인해 두 번 실행되는 것을 방지
            import sys
            if not any(arg.startswith('runserver') for arg in sys.argv):
                return
                
        # 기존 작업들 재로드
        from .models import ReminderSetting
        from .scheduler import scheduler
        
        try:
            scheduler.remove_all_jobs()
            scheduler.start()
            
            # 활성화된 모든 알림 설정 다시 로드
            active_reminders = ReminderSetting.objects.filter(is_active=True)
            for reminder in active_reminders:
                scheduler.schedule_reminder(reminder)
                
            print("Scheduler started and all jobs reloaded successfully")
        except Exception as e:
            print(f"Error initializing scheduler: {str(e)}")