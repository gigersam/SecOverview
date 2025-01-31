from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def dashboard(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'dashboard.html',
        {
            'title':'Dashboard',
            'year':datetime.now().year,
        }
    )
