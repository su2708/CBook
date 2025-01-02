from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import SignupSerializer
from django.contrib.auth import authenticate, logout, get_user_model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

User = get_user_model()

# Create your views here.
@api_view(['POST'])
@authentication_classes([]) # 전역 인증 설정 무시
@permission_classes([AllowAny]) # 전역 IsAuthenticated 설정 무시
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "회원가입이 성공적으로 완료되었습니다."
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

