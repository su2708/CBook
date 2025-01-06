from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import ChatRoomSerializer
from .models import ChatRoom

from django.contrib.auth import authenticate, logout, get_user_model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, get_list_or_404
from datetime import datetime as dt

class ChatListView(APIView):
    permission_classes = [IsAuthenticated]
    
    # 채팅방 생성 
    def post(self, request):        
        serializer = ChatRoomSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user_id=request.user)
            return Response({
                "message": "채팅 방이 새로 생성되었습니다.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)            