from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from slack_sdk import WebClient
import random

class ReminderScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler({
            'apscheduler.timezone': 'Asia/Seoul',
            'apscheduler.job_defaults.coalesce': True,
            'apscheduler.job_defaults.max_instances': 1,
        })
        self.scheduler.add_jobstore(DjangoJobStore(), "default")
        self.slack_client = WebClient(token=settings.SLACK_BOT_TOKEN)
    
    def remove_all_jobs(self):
        """모든 작업 제거"""
        self.scheduler.remove_all_jobs()
    
    def start(self):
        self.scheduler.start()
    
    def shutdown(self):
        """스케줄러 종료"""
        self.scheduler.shutdown()

    @staticmethod
    def send_reminder(test_plan_id, message_style):
        """실제 알림 전송 함수"""
        from .models import ReminderSetting, MessageTemplate
        from testplans.models import TestPlan
        
        try:
            test_plan = TestPlan.objects.get(plan_id=test_plan_id)
            user = test_plan.user_id
            
            templates = MessageTemplate.objects.filter(style=message_style)
            template = random.choice(templates)
            
            message = template.content.format(
                username=user.username,
                test_name=test_plan.test_name,
                test_date=test_plan.test_date
            )
            
            # Slack 클라이언트 초기화
            slack_client = WebClient(token=settings.SLACK_BOT_TOKEN)
            
            # 이메일로 Slack 사용자 찾기
            try:
                result = slack_client.users_lookupByEmail(
                    email=user.email
                )
                slack_user_id = result['user']['id']
                
                # 찾은 사용자 ID로 DM 전송
                slack_client.chat_postMessage(
                    channel=slack_user_id,
                    text=message
                )
                print(f"Message sent successfully to {user.email}")
                
            except Exception as slack_error:
                print(f"Error finding Slack user with email {user.email}: {str(slack_error)}")
                
        except Exception as e:
            print(f"Failed to send message: {str(e)}")
            
    def schedule_reminder(self, reminder_setting):
        """각 ReminderSetting에 대한 작업 스케줄링"""
        job_id = f"reminder_{reminder_setting.reminder_id}"
        
        # 기존 작업이 있다면 제거
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            
        if not reminder_setting.is_active:
            return
            
        # 새로운 작업 스케줄링
        self.scheduler.add_job(
            self.send_reminder,
            trigger=CronTrigger(
                hour=f"{reminder_setting.start_time}-{reminder_setting.end_time}/{reminder_setting.interval_hours}",
                timezone='Asia/Seoul'
            ),
            id=job_id,
            args=[reminder_setting.test_plan.plan_id, reminder_setting.message_style],
            replace_existing=True,
            misfire_grace_time=3600
        )

scheduler = ReminderScheduler()