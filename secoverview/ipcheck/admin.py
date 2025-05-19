from django.contrib import admin
from .models import Ipcheckbgpview, IpcheckAbuseIPDB, IpcheckMISP

@admin.register(Ipcheckbgpview)
class IpcheckbgpviewAdmin(admin.ModelAdmin):
    list_display = [
        'ip',
        'data', 
        'created_at'
    ]
    search_fields = ['ip']
    list_filter = ['ip']

@admin.register(IpcheckAbuseIPDB)
class IpcheckAbuseIPDBAdmin(admin.ModelAdmin):
    list_display = [
        'ip',
        'data', 
        'created_at'
    ]
    search_fields = ['ip']
    list_filter = ['ip']

@admin.register(IpcheckMISP)
class IpcheckMISPAdmin(admin.ModelAdmin):
    list_display = [
        'ip',
        'data', 
        'created_at'
    ]
    search_fields = ['ip']
    list_filter = ['ip']