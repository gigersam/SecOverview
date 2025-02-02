from django.urls import path
from . import views

urlpatterns = [
    path('', views.ransomwarelive, name='ransomwarelive'),
    path('victims', views.victimsoverview, name='victimsoverview'),
    path('victims/<int:id>', views.victimview, name='victimview'),
    path('groups', views.groupsoverview, name='groupsoverview'),
    path('groups/<int:id>', views.groupview, name='groupview'),
]