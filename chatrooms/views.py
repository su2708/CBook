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
            
            if not messages.exists():
                return Response({
                    "message": "아직 대화가 시작되지 않았습니다."
                }, status=status.HTTP_204_NO_CONTENT)
            
            serializer = ChatMsgSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, chat_id):
        """
        새로운 채팅 메시지를 생성 
        """
        try:
            # 필요한 데이터 추출 
            user_msg = request.data.get("user_msg")
            if not user_msg:
                return Response({
                    "message": "'user_msg'는 필수 입력 사항입니다."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # User의 ChatMessage 모델 객체 생성
            new_msg = ChatMessage.objects.create(
                chat_id_id = chat_id,
                message_content = {"content": user_msg},
                sent_by = 'user'
            )
            
            # AI 응답 처리 및 저장 
            ai_response = chatbot(user_msg)["content"]
            ChatMessage.objects.create(
                chat_id_id = chat_id,
                message_content = {"content": ai_response},
                sent_by = "ai"
            )
            
            return Response({
                "message": "메시지가 성공적으로 생성되었습니다.",
                "user_msg": user_msg,
                "ai_response": {"content": ai_response}
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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