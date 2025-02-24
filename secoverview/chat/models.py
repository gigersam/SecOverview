from django.db import models

class ChatMessage(models.Model):
    user_input = models.TextField()
    model_response = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_input[:50]