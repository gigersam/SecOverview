from django.urls import path
from . import views

urlpatterns = [
    path('', views.ipcheck, name='ipcheck'),
]