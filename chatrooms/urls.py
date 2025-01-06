from django.urls import path
from .views import ChatListView

app_name = 'chatrooms'

urlpatterns = [
    path('', ChatListView.as_view(), name='create_chatroom'),
    path('<int:chat_id>/', ChatListView.as_view(), name='get_plan'),
    path('<int:chat_id>/chatmessages/', ChatListView.as_view(), name='get_plan'),
]