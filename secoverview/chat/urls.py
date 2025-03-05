from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatpage, name='chatpage'),
    path("upload/", views.upload_file_view, name="upload"),
]