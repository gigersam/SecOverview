from django.contrib import admin
from .models import CRTSHScan, CRTSHResult, WebHeaderCheck, WebTechFingerprinting_Scan, WebTechFingerprinting_Results

@admin.register(WebHeaderCheck)
class WebHeaderCheckAdmin(admin.ModelAdmin):
    list_display = [
        'domain',
        'scaned_at', 
    ]
    search_fields = ['domain']
    list_filter = ['domain']

@admin.register(CRTSHScan)
class CRTSHScanAdmin(admin.ModelAdmin):
    list_display = [
        'domain',
        'scaned_at', 
    ]
    search_fields = ['domain']
    list_filter = ['domain']

@admin.register(CRTSHResult)
class CRTSHResultAdmin(admin.ModelAdmin):
    list_display = [
        'domain',
        'result', 
    ]
    search_fields = ['domain','result']
    list_filter = ['domain']

@admin.register(WebTechFingerprinting_Scan)
class WebTechFingerprinting_ScanAdmin(admin.ModelAdmin):
    list_display = [
        'domain',
        'scaned_at', 
    ]
    search_fields = ['domain']
    list_filter = ['domain']


@admin.register(WebTechFingerprinting_Results)
class WebTechFingerprinting_ResultsAdmin(admin.ModelAdmin):
    list_display = [
        'domain',
        'technologie',
        'version'
    ]
    search_fields = ['domain','technologie']
    list_filter = ['domain']