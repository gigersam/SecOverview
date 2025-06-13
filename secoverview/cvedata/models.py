from django.db import models

# models.py
class CveItem(models.Model):
    cve_id = models.CharField(max_length=50, primary_key=True)
    source_identifier = models.CharField(max_length=200)
    published = models.DateTimeField()
    last_modified = models.DateTimeField()
    vuln_status = models.CharField(max_length=50)
    descriptions = models.JSONField()
    metrics = models.JSONField()
    weaknesses = models.JSONField()
    configurations = models.JSONField(null=True)
    references = models.JSONField()

    def __str__(self):
        return self.cve_id