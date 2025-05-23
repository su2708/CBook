from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAuthenticated
from langchain_core.messages import HumanMessage, AIMessage

from .serializers import ChatRoomSerializer, ChatMsgSerializer
from .models import ChatRoom, ChatMessage
from .chatbot import chatbot

# 특정 사용자 인증에 대한 class 
class IsOwner(BasePermission):
    def has_permission(self, request, view):
        user_id = view.kwargs.get("user_id")  # URL 매개변수에서 user_id 가져오기 
        
        if not user_id:
            user_id = request.GET.get("user_id")  # 쿼리 문자열에서 user_id 가져오기
        
        if str(request.user.id) == str(user_id):
            return True
        return False

# 채팅방에 대한 class
class ChatListView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        """
        존재하는 채팅 방을 모두 조회 
        """
        # request params에서 user_id 추출. 기본 값은 1
        user_id = request.GET.get('user_id', 1)
        
        try:
            chatrooms = ChatRoom.objects.filter(user_id=user_id)
            
            if not chatrooms.exists():
                return Response({
                    "message": "아직 채팅 방이 없습니다."
                }, status=status.HTTP_204_NO_CONTENT)
            
            serializer = ChatRoomSerializer(chatrooms, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "message": f"채팅방 조회 오류 {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    def post(self, request):
        """
        새로운 채팅 방을 생성 
        """
        # request params에서 user_id 추출. 기본 값은 1
        user_id = request.GET.get('user_id', 1)
        chat_name = request.data.get("chat_name")
        
        if not chat_name:
            return Response({
                "message": "'chat_name'는 필수 입력 사항입니다."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = request.data.copy()
            data["user_id"] = user_id
            data["chat_name"] = chat_name
            
            # 데이터 직렬화
            serializer = ChatRoomSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()            
                return Response({
                    "message": f"{chat_name} 채팅 방이 생성되었습니다.",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                "message": f"채팅방 생성 오류 {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """
        새로운 채팅 방을 생성 
        """
        # request params에서 user_id와 chat_id 추출. 기본 값은 1
        user_id = request.GET.get('user_id', 1)
        chat_id = request.GET.get('chat_id')
        
        if not chat_id:
            return Response({
                "message": "'chat_id'는 필수 입력 사항입니다."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 삭제할 채팅방 검색 
            chatroom = ChatRoom.objects.filter(user_id=user_id, chat_id=chat_id).first()
            
            if not chatroom:
                return Response({
                    "message": f"채팅 방 {chat_id}를 찾을 수 없습니다."
                }, status=status.HTTP_404_NOT_FOUND)
                
            # 채팅방 삭제 
            chatroom.delete()
            return Response({
                "message": f"{chat_id}번 채팅 방이 성공적으로 삭제되었습니다."
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "message": f"채팅 방 삭제 오류: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 채팅 메시지에 대한 class
class ChatMsgListView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get(self, request, user_id):
        """
        특정 채팅방(chat_id)에 해당하는 모든 메시지를 반환 
        """
        # request params에서 chat_id 추출. 기본 값은 1
        chatroom_id = request.GET.get("chatroom_id", 1)
        
        try:
            messages = ChatMessage.objects.filter(user_id=user_id, chatroom_id=chatroom_id).order_by("sent_at")
            
            if not messages.exists():
                return Response({
                    "message": "아직 대화가 시작되지 않았습니다."
                }, status=status.HTTP_204_NO_CONTENT)
            
            serializer = ChatMsgSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "message": f"채팅 메시지 조회 오류 {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, user_id):
        """
        새로운 채팅 메시지를 생성하며, 시험 계획 요청을 처리 
        """
        # request params에서 chat_id 추출. 기본 값은 1
        chatroom_id = request.GET.get("chatroom_id", 1)
        
        try:
            # 클라이언트로부터 필요한 데이터 추출 
            user_msg = request.data.get("user_msg")
            if not user_msg:
                return Response({
                    "message": "'user_msg'는 필수 입력 사항입니다."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 최신 대화 10개 가져오기
            past_messages = ChatMessage.objects.filter(user_id=user_id, chatroom_id=chatroom_id).order_by("-sent_at")[:10]
            
            # 1-1. 과거 대화 내역을 JSON 형태로 정리 (최신 -> 예전 순으로 정렬)
            chat_history = []
            for msg in reversed(past_messages):  # 최신순으로 가져왔으니 순서 뒤집기 
                if msg.sent_by == "user":
                    chat_history.append(
                        # ("human", msg.message_content)
                        HumanMessage(content=msg.message_content)
                    )
                else:
                    if isinstance(msg.message_content, list): # JSON인 경우 OPENAI 입력에 맞게 직렬화 
                        chat_history.append(
                            # ("ai", str(msg.message_content))
                            AIMessage(content=str(msg.message_content))
                        )
                    else:
                        chat_history.append(
                            # ("ai", msg.message_content)
                            AIMessage(content=msg.message_content)
                        )
            
            # 챗봇에게 과거 대화 내역과 새로운 메시지 보내기 
            chatbot_input = {"chat_history": chat_history, "user_msg": user_msg}

            # 테스트용으로 챗봇 출력이 이렇게 된다고 하자.
            action, ai_response = chatbot(chatbot_input)
            
            # 질문과 응답을 chat_id에 저장하기 위한 ChatRoom instance 가져오기 
            chat_room = ChatRoom.objects.filter(user_id=user_id, chat_id=chatroom_id).first()
            
            # user_msg 저장
            ChatMessage.objects.create(
                chat_id = chat_room,  # ChatRoom 객체 저장 
                chatroom_id = chat_room.chat_id,  # ChatRoom의 chat_id를 저장 
                user_id = request.user,
                message_content = user_msg,
                sent_by = 'user', 
                action = ""
            )
            
            # ai_response 저장 
            ChatMessage.objects.create(
                chat_id = chat_room,
                chatroom_id = chat_room.chat_id,
                user_id = request.user,
                message_content = ai_response,
                sent_by = "ai",
                action = action
            )
            
            print(f"ai: {ai_response}")
            print('='*60)
            print(f"chat room: {chat_room.chat_name}")
            
            return Response({
                "message": "메시지가 성공적으로 생성되었습니다.",
                "user_msg": user_msg,
                "ai_response": {
                    "action": action,
                    "content": ai_response
                }
            }, status=status.HTTP_201_CREATED)
        
        except ChatRoom.DoesNotExist:
            return Response({
                "message": "해당 채팅 방을 찾을 수 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                "message": f"채팅 메시지 전송 오류 {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)