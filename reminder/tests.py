from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import ReminderSetting, MessageTemplate
from testplans.models import TestPlan

User = get_user_model()

class ReminderModelTests(TestCase):
    fixtures = ['message_templates.json']
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            phone='01012345678'
        )
        
        self.test_plan = TestPlan.objects.create(
            user_id=self.user,
            test_name='정보처리기사',
            test_date='2024-04-20',
            test_place='서울 강남'
        )
        
        self.reminder_setting = ReminderSetting.objects.create(
            test_plan=self.test_plan,
            start_time=9,
            end_time=18,
            interval_hours=2,
            message_style='encourage'
        )

    def test_reminder_setting_creation(self):
        self.assertEqual(self.reminder_setting.test_plan.test_name, '정보처리기사')
        self.assertEqual(self.reminder_setting.start_time, 9)
        self.assertEqual(self.reminder_setting.end_time, 18)
        self.assertTrue(self.reminder_setting.is_active)

    def test_message_template_exists(self):
        templates = MessageTemplate.objects.filter(style='encourage')
        self.assertTrue(templates.exists())
        self.assertEqual(templates.count(), 3)

class ReminderAPITests(APITestCase):
    fixtures = ['message_templates.json']
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            phone='01012345678'
        )
        self.client.force_authenticate(user=self.user)
        
        self.test_plan = TestPlan.objects.create(
            user_id=self.user,
            test_name='정보처리기사',
            test_date='2024-04-20',
            test_place='서울 강남'
        )
        
        # 스케줄러 모킹 설정
        self.scheduler_patcher = patch('reminder.views.scheduler')
        self.mock_scheduler = self.scheduler_patcher.start()
        
    def tearDown(self):
        self.scheduler_patcher.stop()

    @patch('reminder.scheduler.ReminderScheduler')
    def test_create_reminder_setting(self, mock_scheduler_class):
        """알림 설정 생성 API 테스트"""
        url = '/api/v1/reminder/settings/'
        data = {
            'test_plan': self.test_plan.plan_id,
            'start_time': 9,
            'end_time': 18,
            'interval_hours': 2,
            'message_style': 'encourage'
        }
        
        # 스케줄러 메소드 모킹
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReminderSetting.objects.count(), 1)
        
        # 스케줄러 메소드가 호출되었는지 확인
        self.mock_scheduler.schedule_reminder.assert_called_once()

    def test_get_reminder_settings(self):
        """알림 설정 조회 API 테스트"""
        ReminderSetting.objects.create(
            test_plan=self.test_plan,
            start_time=9,
            end_time=18,
            interval_hours=2,
            message_style='encourage'
        )
        url = '/api/v1/reminder/settings/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_toggle_reminder_setting(self):
        """알림 설정 활성화/비활성화 토글 테스트"""
        reminder = ReminderSetting.objects.create(
            test_plan=self.test_plan,
            start_time=9,
            end_time=18,
            interval_hours=2,
            message_style='encourage'
        )
        url = f'/api/v1/reminder/settings/{reminder.reminder_id}/toggle_active/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reminder.refresh_from_db()
        self.assertFalse(reminder.is_active)
        
        # 스케줄러 메소드가 호출되었는지 확인
        self.mock_scheduler.schedule_reminder.assert_called_once()