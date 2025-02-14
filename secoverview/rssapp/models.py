from django.db import models

class FeedSource(models.Model):
    """Model to store RSS feed sources"""
    url = models.URLField(unique=True)
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class RSSFeed(models.Model):
    """Model to store RSS feed data"""
    title = models.CharField(max_length=255)
    link = models.URLField(unique=True)
    summary = models.TextField()
    source = models.ForeignKey(FeedSource, on_delete=models.CASCADE)  # ForeignKey to FeedSource
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    