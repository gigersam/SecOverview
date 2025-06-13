from django.urls import path
from . import views

urlpatterns = [
    path('', views.cve_view, name='cve_view'),
    path('get', views.get_cve_data, name='get_cve_data'),
    path('<slug:id>', views.cve_details, name='cve_details'),
]