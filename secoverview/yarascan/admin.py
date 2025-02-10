from django.contrib import admin
from .models import ScanResult
# Register your models here.

@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = [
        'uuid', 
        'file_name',
        'stored_file_path', 
        'matched_rules',
        'scanned_at'
    ]
    search_fields = ['file_name']
    list_filter = ['file_name']