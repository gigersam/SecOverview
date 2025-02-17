from django.urls import path
from . import views
from dashboard.views import dashboard

urlpatterns = [
    path('', dashboard, name='index'),
    path('about/', views.about, name='about'),
]