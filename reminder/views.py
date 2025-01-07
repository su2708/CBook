from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ReminderSettings, ReminderMessage
from .serializers import ReminderSettingsSerializer, ReminderMessageSerializer
from testplans.models import TestPlan


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reminder_messages(request):
    """메시지 스타일별 알림 메시지 조회"""
    message_style = request.query_params.get('message_style')
    
    if not message_style:
        return Response({"detail": "message_style은 필수 파라미터입니다."}, 
                       status=status.HTTP_400_BAD_REQUEST)
        
    reminder_messages = ReminderMessage.objects.filter(message_style=message_style)
    serializer = ReminderMessageSerializer(reminder_messages, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def reminder_settings(request, plan_id):
    """알림 설정 조회 및 생성"""
    try:
        test_plan = TestPlan.objects.get(id=plan_id)
    except TestPlan.DoesNotExist:
        return Response({"detail": "시험 계획을 찾을 수 없습니다."}, 
                       status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        try:
            settings = ReminderSettings.objects.get(test_plan=test_plan)
            serializer = ReminderSettingsSerializer(settings)
            return Response(serializer.data)
        except ReminderSettings.DoesNotExist:
            return Response({"detail": "알림 설정이 없습니다."}, 
                          status=status.HTTP_404_NOT_FOUND)

    # POST 요청 처리
    if ReminderSettings.objects.filter(test_plan=test_plan).exists():
        return Response({"detail": "이미 알림 설정이 존재합니다."}, 
                       status=status.HTTP_400_BAD_REQUEST)

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
        return Response({"detail": "알림 설정을 찾을 수 없습니다."}, 
                       status=status.HTTP_404_NOT_FOUND)

    serializer = ReminderSettingsSerializer(settings, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)