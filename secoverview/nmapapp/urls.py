from django.urls import path
from . import views

urlpatterns = [
    path('overview', views.overview, name='nmapoverview'),
    path('scan', views.scan, name='nmapscan'),
    path('scans', views.scansoverview, name='scansoverview'),
    path('scans/<int:id>', views.scanview, name='scanview'),
    path('assets', views.assetsoverview, name='assetsoverview'),
    path('assets/<int:id>', views.assetview, name='assetview'),
]