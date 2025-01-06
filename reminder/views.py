from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ReminderSettings, ReminderTemplate
from .serializers import ReminderSettingsSerializer, ReminderTemplateSerializer
from testplans.models import TestPlan


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reminder_templates(request):
    """알림 템플릿 목록 조회"""
    message_style = request.query_params.get('message_style')
    reminder_templates = ReminderTemplate.objects.filter(message_style=message_style) if message_style else ReminderTemplate.objects.all()
    serializer = ReminderTemplateSerializer(reminder_templates, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def reminder_settings(request, plan_id):
    """알림 설정 조회 및 생성"""
    try:
        test_plan = TestPlan.objects.get(id=plan_id)
    except TestPlan.DoesNotExist:
        return Response({"detail": "TestPlan이 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 알림 설정 조회
    if request.method == 'GET':
        try:
            settings = ReminderSettings.objects.get(test_plan=test_plan)
            serializer = ReminderSettingsSerializer(settings)
            return Response(serializer.data)
        except ReminderSettings.DoesNotExist:
            return Response({"detail": "알림 설정이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 알림 설정 생성
    if ReminderSettings.objects.filter(test_plan=test_plan).exists():
        return Response({"detail": "이미 알림 설정이 존재합니다."}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ReminderSettingsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(test_plan=test_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_reminder_settings(request, plan_id):
    """알림 설정 수정"""
    try:
        settings = ReminderSettings.objects.get(test_plan_id=plan_id)
    except ReminderSettings.DoesNotExist:
        return Response({"detail": "알림 설정이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ReminderSettingsSerializer(settings, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
