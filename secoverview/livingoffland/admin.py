from django.contrib import admin
from .models import LOLBASBinary, LOLBASCommand, LOLBASTag, LOLBASFullPath, LOLBASResource, LOLBASDetection, GTFObinsBinary, GTFObinsFunction, GTFObinsFunctionExample

@admin.register(LOLBASBinary)
class LOLBASBinaryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'description',
        'author',
        'created',
        'url',
    ]
    search_fields = ['name']
    list_filter = ['name']

@admin.register(LOLBASCommand)
class LOLBASCommandAdmin(admin.ModelAdmin):
    list_display = [
        'binary',
        'command', 
        'description',
        'usecase',
        'category',
        'privileges',
        'mitre_id',
        'operating_system',
    ]
    search_fields = ['binary','vacommandlue']
    list_filter = ['binary']

@admin.register(LOLBASTag)
class LOLBASTagAdmin(admin.ModelAdmin):
    list_display = [
        'value',
        'command',
        'key',
    ]
    search_fields = ['command']
    list_filter = ['command']

@admin.register(LOLBASFullPath)
class LOLBASFullPathAdmin(admin.ModelAdmin):
    list_display = [
        'path',
        'binary',
    ]
    search_fields = ['path']
    list_filter = ['path']

@admin.register(LOLBASDetection)
class LOLBASDetectionAdmin(admin.ModelAdmin):
    list_display = [
        'value',
        'binary',
        'key',
    ]
    search_fields = ['value']
    list_filter = ['value']

@admin.register(LOLBASResource)
class LOLBASResourceAdmin(admin.ModelAdmin):
    list_display = [
        'link',
        'binary',
    ]
    search_fields = ['binary']
    list_filter = ['binary']

@admin.register(GTFObinsBinary)
class GTFObinsBinaryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'description',
    ]
    search_fields = ['name']
    list_filter = ['name']

@admin.register(GTFObinsFunction)
class GTFObinsFunctionAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'description',
    ]
    search_fields = ['name']
    list_filter = ['name']

@admin.register(GTFObinsFunctionExample)
class GTFObinsFunctionExampleAdmin(admin.ModelAdmin):
    list_display = [
        'binary',
        'function',
        'description',
        'code',
    ]
    search_fields = ['binary']
    list_filter = ['binary']