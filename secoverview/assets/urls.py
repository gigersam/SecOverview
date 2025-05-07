from django.urls import path
from . import views

urlpatterns = [
    path('overview', views.assetsoverview, name='assetsoverview'),
    path('asset/<int:id>', views.assetview, name='assetview'),
]