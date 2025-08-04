from django.db import models
from django.db.models import Prefetch

class LOLBASBinaryQuerySet(models.QuerySet):
    def with_all_related(self):
        return self.prefetch_related(
            Prefetch(
                "commands",
                queryset=LOLBASCommand.objects.prefetch_related("tags"),
            ),
            "full_paths",
            "detections",
            "resources",
        )

class GTFObinsBinaryQuerySet(models.QuerySet):
    def with_all_related(self):
        return self.prefetch_related("function_examples__function")

class LOLBASBinary(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    author = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
 
    objects = LOLBASBinaryQuerySet.as_manager()

    def __str__(self):
        return self.name or "Unnamed Binary"


class LOLBASCommand(models.Model):
    binary = models.ForeignKey(LOLBASBinary, on_delete=models.CASCADE, related_name="commands", null=True, blank=True)
    command = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    usecase = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    privileges = models.CharField(max_length=255, null=True, blank=True)
    mitre_id = models.CharField(max_length=50, null=True, blank=True)
    operating_system = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.command or "Unnamed Command"


class LOLBASTag(models.Model):
    command = models.ForeignKey(LOLBASCommand, on_delete=models.CASCADE, related_name="tags", null=True, blank=True)
    key = models.CharField(max_length=255, null=True, blank=True)
    value = models.CharField(max_length=255, null=True, blank=True)


class LOLBASFullPath(models.Model):
    binary = models.ForeignKey(LOLBASBinary, on_delete=models.CASCADE, related_name="full_paths", null=True, blank=True)
    path = models.TextField(null=True, blank=True)


class LOLBASDetection(models.Model):
    binary = models.ForeignKey(LOLBASBinary, on_delete=models.CASCADE, related_name="detections", null=True, blank=True)
    key = models.CharField(max_length=255, null=True, blank=True)   # Sigma, Splunk, IOC, etc.
    value = models.TextField(null=True, blank=True)


class LOLBASResource(models.Model):
    binary = models.ForeignKey(LOLBASBinary, on_delete=models.CASCADE, related_name="resources", null=True, blank=True)
    link = models.URLField(null=True, blank=True)

class GTFObinsBinary(models.Model):
    """
    Stores each GTFOBins binary (e.g., awk, vim, find).
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    objects = GTFObinsBinaryQuerySet.as_manager()

    def __str__(self):
        return self.name or "Unnamed Binary"


class GTFObinsFunction(models.Model):
    """
    Master list of functions (Shell, Reverse shell, File upload, etc.).
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name or "Unnamed Function"


class GTFObinsFunctionExample(models.Model):
    """
    Stores each example (code + description) for a function related to a binary.
    """
    binary = models.ForeignKey(GTFObinsBinary, on_delete=models.CASCADE, related_name="function_examples", null=True, blank=True)
    function = models.ForeignKey(GTFObinsFunction, on_delete=models.CASCADE, related_name="examples", null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    code = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.function} Example" if self.function else "Example"