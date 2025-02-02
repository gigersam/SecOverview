from django.contrib import admin
from .models import Nmapscan, Assets
@admin.register(Nmapscan)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'data', 
        'ip',
        'parameters', 
        'created_at'
    ]
    search_fields = ['ip']
    list_filter = ['ip']

@admin.register(Assets)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'hostname', 
        'ip_address'
    ]
    search_fields = ['ip_address']
    list_filter = ['ip_address']