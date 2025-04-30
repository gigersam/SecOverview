from django.contrib import admin
from .models import Nmapscan, NmapAssets, AssetsNmapscan

@admin.register(Nmapscan)
class NmapscanAdmin(admin.ModelAdmin):
    list_display = [
        'data', 
        'ip',
        'parameters', 
        'created_at'
    ]
    search_fields = ['ip']
    list_filter = ['ip']

@admin.register(NmapAssets)
class NmapAssetsAdmin(admin.ModelAdmin):
    list_display = [
        'hostname', 
        'ip_address'
    ]
    search_fields = ['ip_address']
    list_filter = ['ip_address']

@admin.register(AssetsNmapscan)
class AssetsNmapscanAdmin(admin.ModelAdmin):
    list_display = [
        'assets', 
        'nmapscan'
    ]
    search_fields = ['assets']
    list_filter = ['assets']