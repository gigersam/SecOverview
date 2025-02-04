from django.db import models

class DNSQuery(models.Model):
    domain = models.CharField(max_length=255, help_text="Domain name being queried")
    query_time = models.DateTimeField(auto_now_add=True, help_text="Timestamp of the query")

    def __str__(self):
        return f"Query for {self.domain} at {self.query_time}"

class DNSRecord(models.Model):
    RECORD_TYPES = [
        ('A', 'A'),
        ('AAAA', 'AAAA'),
        ('CNAME', 'CNAME'),
        ('MX', 'MX'),
        ('TXT', 'TXT'),
        ('NS', 'NS'),
        ('SOA', 'SOA'),
        ('PTR', 'PTR'),
        ('SRV', 'SRV'),
    ]
    
    query = models.ForeignKey(DNSQuery, on_delete=models.CASCADE, related_name="records")
    record_type = models.CharField(max_length=10, choices=RECORD_TYPES, help_text="Type of DNS record")
    value = models.CharField(max_length=1024, help_text="DNS record value")
    ttl = models.PositiveIntegerField(default=3600, help_text="Time to Live (TTL) in seconds")
    
    def __str__(self):
        return f"{self.record_type} record for {self.query.domain}: {self.value} (TTL: {self.ttl})"