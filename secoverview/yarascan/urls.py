from django.urls import path
from . import views

urlpatterns = [
    path('', views.yara_scan_view, name='yara_scan_view'),
    path('overview', views.yara_scan_overview, name='yara_scan_overview'),
    path('overview/<slug:uuid>', views.yarascanreport, name='yarascanreport'),
]