from django.contrib import admin
from .models import ComputeAssets, ComputeAssetsNetworkPorts, ComputeAssetsNetworkDetection, ComputeAssetsCVE

# Register your models here.

@admin.register(ComputeAssets)
class ComputeAssetsAdmin(admin.ModelAdmin):
    list_display = [
        'hostname', 
        'ip_address', 
        'description', 
        'asset_classification', 
        'threat_level'
    ]
    search_fields = ['hostname', 'ip_address']
    list_filter = ['asset_classification']

@admin.register(ComputeAssetsNetworkPorts)
class ComputeAssetsNetworkPortsAdmin(admin.ModelAdmin):
    list_display = [
        'port_number', 
        'service', 
        'product', 
        'version', 
        'extrainfo',
        'cpe', 
        'detection_severity'
    ]
    search_fields = ['port_number', 'service', 'product', 'version', 'extrainfo']
    list_filter = ['detection_severity']

@admin.register(ComputeAssetsNetworkDetection)
class ComputeAssetsNetworkDetectionAdmin(admin.ModelAdmin):
    list_display = [
        'compute_assets', 
        'mlnids_detection', 
        'detection_severity', 
    ]
    search_fields = ['mlnids_detection', 'compute_assets']
    list_filter = ['detection_severity']

@admin.register(ComputeAssetsCVE)
class ComputeAssetsCVEAdmin(admin.ModelAdmin):
    list_display = [
        'compute_assets', 
        'cve', 
    ]
    search_fields = ['cve', 'compute_assets']
    list_filter = ['compute_assets']