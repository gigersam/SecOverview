from django.urls import path
from . import views

urlpatterns = [
    path('', views.web_overview, name='web_overview'),
]