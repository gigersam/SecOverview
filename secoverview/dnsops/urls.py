from django.urls import path
from . import views

urlpatterns = [
    path('', views.dnsoverview, name='dnsoverview'),
]