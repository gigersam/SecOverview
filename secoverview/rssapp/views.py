from django.shortcuts import render
from django.http import HttpRequest
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import RSSFeed, FeedSource
from django.db.models import Q
import requests
import re
import xml.etree.ElementTree as ET
import json


def fetch_rss_feed(query):
    """Fetch and parse multiple RSS feeds using native XML parsing"""
    feed_items = []
    if query == None or query == "":
        feed_sources = FeedSource.objects.all()

        for feed_source in feed_sources:
            try:
                response = requests.get(feed_source.url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"})
                root = ET.fromstring(response.content)
                items = root.findall(".//item")

                for item in items:
                    title = item.find("title").text if item.find("title") is not None else "No Title"
                    link = item.find("link").text if item.find("link") is not None else "#"
                    description = item.find("description").text if item.find("description") is not None else "No Description"
                    rmhtml = re.compile('<.*?>') 
                    description = re.sub(rmhtml, '', description)
                    # Store in database if not already present
                    if not RSSFeed.objects.filter(link=link).exists():
                        RSSFeed.objects.create(title=title, link=link, summary=description, source=feed_source)
            except Exception as e:
                print(f"Error fetching {feed_source.name}: {e}")

        feed_items = RSSFeed.objects.order_by('-pub_date')
    else:
        feed_items = RSSFeed.objects.filter(Q(title__icontains=query) | Q(link__icontains=query) | Q(summary__icontains=query) | Q(pub_date__icontains=query)).order_by('-pub_date')
    
    return feed_items  # List of parsed feed entries

@login_required
def rss_feed_view(request):
    """View to display RSS feed data"""
    assert isinstance(request, HttpRequest)
    query = request.GET.get("search")
    feed_items = fetch_rss_feed(query)
    paginator = Paginator(feed_items, 5)
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the appropriate page of blog posts

    return render(
        request, 
        "rss_feed.html", 
        {
            'title':'Ransomwarelive Victims Overview',
            'year':datetime.now().year,
            "feed_items": page_obj,
            'chatcontext':"This page shows RSS-Feeds. Feeds-Data: " + str(page_obj.object_list)
        })
