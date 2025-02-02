from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('ransomwarelive/groups/fetch', views.fetch_groups, name='ransomware_fetch_groups'),
    path('ransomwarelive/victims/fetch', views.fetch_victims, name='ransomware_fetch_victims'),
    path('nmap/scan', views.nmap_scan, name='nmap_scan'),
    path('logout', views.logout_view, name='logout'),
]