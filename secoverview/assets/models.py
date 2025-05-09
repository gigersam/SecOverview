from django.db import models
from nmapapp.models import NmapAssets, Nmapscan, AssetsNmapscan
from mlnids.models import NetworkFlow

# Create your models here.

class ComputeAssets(models.Model):
    hostname = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    description = models.TextField(blank=True, null=True)
    asset_classification = models.IntegerField(choices=[(1, 'Negligible'), (2, 'Low'), (3, 'Medium'), (4, 'High'), (5, 'Critical')], default=1)
    threat_level = models.IntegerField(choices=[(1, 'Negligible'), (2, 'Low'), (3, 'Medium'), (4, 'High'), (5, 'Critical')], default=1)
    nmap_asset = models.ForeignKey(NmapAssets, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.ip_address
    
    def context_string(self):
        return (f"Hostname: {self.hostname} , IP Address: {self.ip_address} , asset classification: {str(self.asset_classification)}, threat level: {str(self.threat_level)}")

class ComputeAssetsNetworkPorts(models.Model):
    port_number  = models.IntegerField(max_length=255)
    service  = models.CharField(max_length=255, null=True)
    product  = models.CharField(max_length=255, blank=True, null=True)
    version  = models.CharField(max_length=255, blank=True, null=True)
    extrainfo = models.CharField(max_length=255, blank=True, null=True)
    cpe = models.CharField(max_length=255, blank=True, null=True)
    detection_severity = models.IntegerField(choices=[(1, 'Negligible'), (2, 'Low'), (3, 'Medium'), (4, 'High'), (5, 'Critical')], default=1)
    asset = models.ForeignKey(ComputeAssets, on_delete=models.CASCADE)

    def __str__(self):
        return str(f"Port: {self.port_number}, Service: {self.service}, Product: {self.product}, Version: {self.version}, Extra Info: {self.extrainfo}, CPE: {self.cpe}, detection severity: {self.detection_severity}")

class ComputeAssetsNetworkDetection(models.Model):
    mlnids_detection = models.ForeignKey(NetworkFlow, on_delete=models.SET_NULL, blank=True, null=True)
    detection_severity = models.IntegerField(choices=[(1, 'Negligible'), (2, 'Low'), (3, 'Medium'), (4, 'High'), (5, 'Critical')], default=1)
    compute_assets = models.ForeignKey(ComputeAssets, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(f"MLNIDS Detection: {self.mlnids_detection}, Severity: {self.detection_severity}")
