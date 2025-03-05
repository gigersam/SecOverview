from django.contrib import admin
from .models import APIData, ChatMessage, RAGPool, UploadedFile

@admin.register(ChatMessage)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'user_input', 
        'model_response',
    ]
    search_fields = ['user_input']
    list_filter = ['user_input']

@admin.register(RAGPool)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'RAGPoolName', 
        'uuid',
    ]
    search_fields = ['RAGPoolName','uuid']
    list_filter = ['RAGPoolName']

@admin.register(UploadedFile)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'rag_pool', 
        'file',
    ]
    search_fields = ['rag_pool','file']
    list_filter = ['file']

@admin.register(APIData)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'rag_pool', 
        'name',
        'base_url',
        'description',
        'created_at',
        'updated_at',
    ]
    search_fields = ['rag_pool','name','base_url','descrition']
    list_filter = ['rag_pool']