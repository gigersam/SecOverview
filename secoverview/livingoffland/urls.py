from django.urls import path
from . import views

urlpatterns = [
    path('', views.livingoffland, name='livingoffland'),
    path('update', views.livingofflandupdate, name='livingofflandupdate'),
    path('binary/windows/<int:binary>', views.livingofflandbinary, name='livingofflandbinary'),
    path('binary/linux/<int:binary>', views.gtfobinsbinary, name='gtfobinsbinary'),
    path('commandsearcher', views.livingofflandcommandsearch, name='livingofflandcommandsearch'),
]