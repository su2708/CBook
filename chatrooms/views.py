from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import ChatRoomSerializer, ChatMsgSerializer
from .models import ChatRoom, ChatMessage

from django.contrib.auth import authenticate, logout, get_user_model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, get_list_or_404
from datetime import datetime as dt
from .chatbot import chatbot

# 채팅 메시지에 대한 class
class ChatMsgListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, chat_id):
        """
        특정 채팅방(chat_id)에 해당하는 모든 메시지를 반환 
        """
        try:
            messages = ChatMessage.objects.filter(chat_id=chat_id).order_by("sent_at")
            serializer = ChatMsgSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ChatMessage.DoesNotExist:
            return Response({
                "message": "아직 대화가 시작되지 않았습니다."
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                "error": {e}
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, chat_id):
        """
        새로운 채팅 메시지를 생성 
        """
        data = request.data
        print(data)
        data['chat_id'] = chat_id  # 요청 데이터에 chat_id 추가 
        response = chatbot(data["user_msg"])
        serializer = ChatMsgSerializer(data=data)
        
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({
                "message": "메시지가 전송되었습니다.",
                "data": {serializer.data}
            }, status=status.HTTP_201_CREATED)


# 채팅방에 대한 class
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