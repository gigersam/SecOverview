from django.urls import path
from . import views

urlpatterns = [
    path('', views.ipcheckbgpview, name='ipcheckbgpview'),
]