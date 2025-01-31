from django.shortcuts import render
from django.http import HttpRequest
from datetime import datetime

def ransomwarelive(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'ransomwarelive.html',
        {
            'title':'Ransomware.live',
            'year':datetime.now().year,
        }
    )