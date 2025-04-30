from django.contrib import admin
from .models import NetworkFlow, RfPrediction

@admin.register(NetworkFlow)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'src_ip', 
        'dst_ip',
        'src_port', 
        'dst_port',
        'protocol', 
        'rf_prediction',
        'if_anomaly_score',
        'if_is_anomaly'
    ]
    search_fields = ['src_ip','dst_ip''src_port','dst_port''protocol','rf_prediction''if_anomaly_score','if_is_anomaly']
    list_filter = ['src_ip']

@admin.register(RfPrediction)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'label', 
        'description',
    ]
    search_fields = ['label']
    list_filter = ['label']


# Register your models here.
