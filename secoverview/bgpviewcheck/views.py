from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from datetime import datetime
import requests

@login_required
def ipcheckbgpview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        ip = request.POST.get('ip')
        response = requests.get(f"https://api.bgpview.io/ip/{ip}")
        response = response.json()
        return render(
            request,
            'ipcheckbgpview.html',
            {
                'title':'IP Check bgpview',
                'year':datetime.now().year,
                'response':response['data']
            }
        )
    else:
        return render(
            request,
            'ipcheckbgpview.html',
            {
                'title':'IP Check bgpview',
                'year':datetime.now().year,
                'response':""
            }
        )
