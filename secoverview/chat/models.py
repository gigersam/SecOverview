import uuid
from django.contrib.auth.models import Group
from django.db import models

class ChatMessage(models.Model):
    user_input = models.TextField()
    model_response = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_input[:50]
    
class RAGPool(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    RAGPoolName = models.CharField(max_length=255)

    def __str__(self):
        return self.RAGPoolName

class UploadedFile(models.Model):
    rag_pool = models.ForeignKey(RAGPool, on_delete=models.CASCADE)  # Link to RAGPool
    file = models.FileField(upload_to="ragpool/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} ({self.rag_pool.RAGPoolName})"

class APIData(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="A unique name for the API")
    rag_pool = models.ForeignKey(RAGPool, on_delete=models.CASCADE)  # Link to RAGPool
    base_url = models.URLField(help_text="The base URL of the API")
    api_key = models.CharField(max_length=512, help_text="The API key for authentication")
    description = models.TextField(blank=True, null=True, help_text="A brief description of the API")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "API Configuration"
        verbose_name_plural = "API Configurations"

    def __str__(self):
        return self.name
    
class RAGGroup(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    rag_pool = models.ManyToManyField(RAGPool, related_name="groups")  # Link to RAGPool
