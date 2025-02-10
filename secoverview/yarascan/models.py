import uuid
from django.db import models

class ScanResult(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    file_name = models.CharField(max_length=255)
    stored_file_path = models.CharField(max_length=255)
    matched_rules = models.TextField()
    scanned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan {self.uuid} - {self.file_name}"
