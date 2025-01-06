from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import ProgressSerializer

from django.contrib.auth import authenticate, logout, get_user_model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from datetime import datetime as dt

User = get_user_model()

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def progress(request, user_id):
    user = request.user  # JWT 인증을 통해 얻은 현재 사용자
    
    if request.method == 'GET':
        serializer = ProgressSerializer(user, context={'request': request})
        return Response(serializer.data, status=200)
    
    if request.method == 'PUT':
        serializer = ProgressSerializer(instance=user, data=request.data, partial=True)  # partial=True로 일부 업데이트 허용

        if serializer.is_valid():
            serializer.save()  # 수정 내용 저장
            return Response({
                "message": "회원정보가 성공적으로 수정되었습니다.",
                "user": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)