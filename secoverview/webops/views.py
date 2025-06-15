from django.shortcuts import render
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def web_overview(request):
    """View to display RSS feed data"""
    assert isinstance(request, HttpRequest)
    query = request.GET.get("search")
    return render(
        request, 
        "web_overview.html", 
        {
            'title':'Web Ops Overview',
            'year':datetime.now().year,
            'chatcontext':"This page "
        })
