from django.shortcuts import render
from django.http import HttpRequest
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def backupoverview(request):
    """View to display RSS feed data"""
    assert isinstance(request, HttpRequest)
    return render(
        request, 
        "backupoverview.html", 
        {
            'title':'Backup Overview',
            'year':datetime.now().year,
            'chatcontext':""
        })
