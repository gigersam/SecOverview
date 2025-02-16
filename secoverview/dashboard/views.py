from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from datetime import datetime
from nmapapp.models import Nmapscan
from ransomwarelive.models import RansomwareliveVictim
from rssapp.models import RSSFeed
from yarascan.models import ScanResult

@login_required
def dashboard(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    scans = Nmapscan.objects.order_by('-id')[:5]
    victims = RansomwareliveVictim.objects.order_by('-id')[:5]
    feed_items = RSSFeed.objects.order_by('-pub_date')[:5]
    filescanresults = ScanResult.objects.exclude(matched_rules="").order_by('-id')[:5]
    return render(
        request,
        'dashboard.html',
        {
            'title':'Dashboard',
            'year':datetime.now().year,
            'scans':scans,
            'victims':victims,
            'feed_items':feed_items,
            'filescanresults':filescanresults
        }
    )
