from django.urls import path
from . import views

urlpatterns = [
    path('', views.rss_feed_view, name='rss_feed_view'),
]