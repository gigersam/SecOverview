from django.urls import path
from . import views

urlpatterns = [
    path('', views.backupoverview, name='backupoverview'),
]