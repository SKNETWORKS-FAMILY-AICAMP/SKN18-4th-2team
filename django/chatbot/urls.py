from django.urls import path

from . import views


app_name = "chatbot"

urlpatterns = [
    path("", views.chatbot_home, name="home"),
    path("chat/", views.chatbot_chat, name="chat"),
    path("chat/conversation/", views.chatbot_conversation, name="chat-detail"),
    path("api/ask/", views.chatbot_ask, name="api-ask"),
]
