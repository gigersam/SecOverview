from django.urls import path
from . import views

urlpatterns = [
    path('overview', views.mlnidsoverview, name='mlnidsoverview'),
    path('detection/<int:pk>', views.mlnidsdetection, name='mlnidsdetection'),
]