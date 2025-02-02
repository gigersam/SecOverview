from django.shortcuts import render
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
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