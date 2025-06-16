from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('ransomwarelive/groups/fetch', views.fetch_groups, name='ransomware_fetch_groups'),
    path('ransomwarelive/victims/fetch', views.fetch_victims, name='ransomware_fetch_victims'),
    path('rssapp/feeds/update', views.rss_feed_update, name='rss_feed_update'),
    path('nmap/scan', views.nmap_scan, name='nmap_scan'),
    path('mlnids/upload', views.mlnids_upload_csv, name='mlnids_upload_csv'),
    path('assets/gather/all', views.assets_gather_all, name='assets_gather_all'),
    path('cve/daily/get', views.cve_get_daily, name='cve_get_daily'),
    path('dns/enumerate', views.api_dns_enumerate, name='api_dns_enumerate'),
    path('web/crt/get', views.api_crtsh_get, name='api_crtsh_get'),
    path('web/webheaders/get', views.api_webheaders_get, name='api_webheaders_get'),
    path('web/webtechfingerprinting/get', views.api_webfingerprinting_get, name='api_webfingerprinting_get'),
    path('web/all/get', views.api_weball_get, name='api_weball_get'),
    path('logout', views.logout_view, name='logout_api'),
]