from django.db import models

class CRTSHScan(models.Model):
    domain = models.CharField(max_length=255)
    scaned_at = models.DateTimeField(auto_now_add=True)

class CRTSHResult(models.Model):
    domain = models.ForeignKey(CRTSHScan, on_delete=models.CASCADE)
    result = models.TextField(max_length=255)

class WebHeaderCheck(models.Model):
    domain = models.CharField(max_length=255)
    scaned_at = models.DateTimeField(auto_now_add=True)
    hsts_detected = models.BooleanField(default=False) 
    hsts_value = models.TextField(null=True, blank=True, default=None)
    hsts_issues = models.TextField(null=True, blank=True, default=None)
    xframeoptions_detected = models.BooleanField(default=False)
    xframeoptions_value = models.TextField(null=True, blank=True, default=None)
    xframeoptions_issues = models.TextField(null=True, blank=True, default=None)
    xcontenttypeoptions_detected = models.BooleanField(default=False)
    xcontenttypeoptions_value = models.TextField(null=True, blank=True, default=None)
    xcontenttypeoptions_issues = models.TextField(null=True, blank=True, default=None)
    csp_detected = models.BooleanField(default=False)
    csp_value = models.TextField(null=True, blank=True, default=None)
    csp_issues = models.TextField(null=True, blank=True, default=None)
    refferrerpolicy_detected = models.BooleanField(default=False)
    refferrerpolicy_value = models.TextField(null=True, blank=True, default=None)
    refferrerpolicy_issues = models.TextField(null=True, blank=True, default=None)
    xssprotection_detected = models.BooleanField(default=False)
    xssprotection_value = models.TextField(null=True, blank=True, default=None)
    xssprotection_issues = models.TextField(null=True, blank=True, default=None)
    permissionspolicy_detected = models.BooleanField(default=False)
    permissionspolicy_value = models.TextField(null=True, blank=True, default=None)
    permissionspolicy_issues = models.TextField(null=True, blank=True, default=None)
    clearsite_detected = models.BooleanField(default=False)
    clearsite_value = models.TextField(null=True, blank=True, default=None)
    clearsite_issues = models.TextField(null=True, blank=True, default=None)
    crossoriginopenerpolicy_detected = models.BooleanField(default=False)
    crossoriginopenerpolicy_value = models.TextField(null=True, blank=True, default=None)
    crossoriginopenerpolicy_issues = models.TextField(null=True, blank=True, default=None)
    crossoriginembedderpolicy_detected = models.BooleanField(default=False)
    crossoriginembedderpolicy_value = models.TextField(null=True, blank=True, default=None)
    crossoriginembedderpolicy_issues = models.TextField(null=True, blank=True, default=None)
    
class WebTechFingerprinting_Scan(models.Model):
    domain = models.CharField(max_length=255)
    scaned_at = models.DateTimeField(auto_now_add=True)

class WebTechFingerprinting_Results(models.Model):
    domain = models.ForeignKey(WebTechFingerprinting_Scan, on_delete=models.CASCADE)
    technologie = models.CharField(max_length=100)
    version = models.TextField(null=True, blank=True, default=None)