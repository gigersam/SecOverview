from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChartAdmin(admin.ModelAdmin):
    list_display = [
        'user_input', 
        'model_response',
    ]
    search_fields = ['user_input']
    list_filter = ['user_input']