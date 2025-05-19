from django.db import models

class IpcheckMISP(models.Model):
    data = models.JSONField(null=True, default=None)
    ip = models.CharField(max_length=45, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Record {self.id} - IP: {self.ip or 'N/A'}"
    

class IpcheckAbuseIPDB(models.Model):
    data = models.JSONField(null=True, default=None)
    ip = models.CharField(max_length=45, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Record {self.id} - IP: {self.ip or 'N/A'}"
    
class Ipcheckbgpview(models.Model):
    data = models.JSONField(null=True, default=None)
    ip = models.CharField(max_length=45, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Record {self.id} - IP: {self.ip or 'N/A'}"