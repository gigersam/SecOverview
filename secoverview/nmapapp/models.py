from django.db import models

class Nmapscan(models.Model):
    data = models.JSONField()  # Stores JSON data
    ip = models.CharField(max_length=45, null=True)  # Supports both single IP and IP range
    parameters = models.JSONField(blank=True, null=True)  # Additional parameters (optional)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when record is created

    def __str__(self):
        return f"Record {self.id} - IP: {self.ip or 'N/A'}"
    
class NmapAssets(models.Model):
    hostname = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    json_data = models.JSONField(blank=True, null=True)
    added_by_scan = models.ForeignKey(Nmapscan, on_delete=models.CASCADE, related_name='scan')

    def __str__(self):
        return self.ip_address

class AssetsNmapscan(models.Model):
    assets = models.ForeignKey(NmapAssets, on_delete=models.CASCADE)
    assets_json_data = models.JSONField(blank=True, null=True)
    nmapscan = models.ForeignKey(Nmapscan, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"Record {self.id} - IP: {self.assets or 'N/A'}"