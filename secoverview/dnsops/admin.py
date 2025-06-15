from django.contrib import admin
from .models import DNSQuery, DNSRecord

@admin.register(DNSQuery)
class DNSQueryAdmin(admin.ModelAdmin):
    list_display = [
        'domain',
        'query_time', 
    ]
    search_fields = ['domain']
    list_filter = ['domain']

@admin.register(DNSRecord)
class DNSRecordAdmin(admin.ModelAdmin):
    list_display = [
        'query',
        'record_type', 
        'value',
        'ttl'
    ]
    search_fields = ['query','value']
    list_filter = ['record_type']