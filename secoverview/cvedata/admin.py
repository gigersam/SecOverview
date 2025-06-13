from django.contrib import admin
from .models import CveItem

@admin.register(CveItem)
class IpcheckbgpviewAdmin(admin.ModelAdmin):
    list_display = [
        'cve_id',
        'vuln_status', 
    ]
    search_fields = ['cve_id']
    list_filter = ['vuln_status']