from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def assetsoverview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'assetsoverview.html',
        {
            'title':'Assets',
            'year':datetime.now().year,
            'chatcontext':"Shows ML analysed detections on the network." 
        }
    )

