from django.shortcuts import render
from django.http import HttpRequest
from datetime import datetime

def index(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'index.html',
        {
            'title':'Home',
            'year':datetime.now().year,
        }
    )