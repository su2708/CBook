from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import TestPlanSerializer
from .models import TestPlan

from django.contrib.auth import authenticate, logout, get_user_model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, get_list_or_404
from datetime import datetime as dt

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_plan(request):
    serializer = TestPlanSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        serializer.save(user_id=request.user)
        return Response({
            "message": "시험 계획 생성 성공"
        }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_plan(request, user_id):
    plans = TestPlan.objects.filter(user_id=user_id)
    serializer = TestPlanSerializer(plans, many=True)
    if request.user.id == serializer.data[0]["user_id"]:
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({"message": "해당하는 사용자가 아닙니다."}, status=status.HTTP_403_FORBIDDEN)
