from django.urls import path
from .views import chatbot, home, speech, login, register, logout, text_to_speech, speech_to_text
from django.contrib import admin
from . import consumers

urlpatterns = [
    path('', home, name='home'),
    path('chatbot/', chatbot, name='chatbot'),
    path('speech/', speech, name='speech'),
    path('login/', login, name='login'),
    #path('whisper_stream/', whisper_stream, name='whisper_stream'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),
    path('text_to_speech/', text_to_speech, name='text_to_speech'),
    path('speech_to_text/', speech_to_text, name='speech_to_text'),
    path("ws/socketserver/", consumers.ChatConsumer.as_asgi()),

]
