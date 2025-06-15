from django.db import models

# models.py
class CveItem(models.Model):
    cve_id = models.CharField(max_length=50, primary_key=True)
    source_identifier = models.CharField(max_length=200)
    published = models.CharField(max_length=64)
    last_modified = models.CharField(max_length=64)
    vuln_status = models.CharField(max_length=50)
    descriptions = models.JSONField()
    metrics = models.JSONField()
    weaknesses = models.JSONField()
    configurations = models.JSONField(null=True)
    references = models.JSONField()

    def __str__(self):
        return self.cve_id