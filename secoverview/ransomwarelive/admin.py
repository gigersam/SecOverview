from django.contrib import admin
from .models import RansomwareliveGroupsGroup, RansomwareliveGroupsLocation, RansomwareliveGroupsProfile, RansomwareliveVictim
# Register your models here.

@admin.register(RansomwareliveGroupsGroup)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'captcha',
        'parser', 
        'javascript_render',
        'meta', 
        'description'
    ]
    search_fields = ['name']
    list_filter = ['name']

@admin.register(RansomwareliveGroupsLocation)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'group', 
        'fqdn',
        'title', 
        'version',
        'slug', 
        'available',
        'updated',
        'lastscrape',
        'enabled'
    ]
    search_fields = ['group']
    list_filter = ['group']

@admin.register(RansomwareliveGroupsProfile)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'group', 
        'link'
    ]
    search_fields = ['group']
    list_filter = ['group']

@admin.register(RansomwareliveVictim)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'post_title', 
        'discovered',
        'published', 
        'post_url',
        'country', 
        'activity',
        'website',
        'description',
        'group'
    ]
    search_fields = ['post_title']
    list_filter = ['post_title']
