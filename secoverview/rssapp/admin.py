from django.contrib import admin
from .models import RSSFeed, FeedSource

@admin.register(RSSFeed)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'link',
        'summary', 
        'pub_date',
        'source',
    ]
    search_fields = ['title','summary']
    list_filter = ['source']

@admin.register(FeedSource)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'url',
    ]
    search_fields = ['name','url']
    list_filter = ['name']
