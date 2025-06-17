from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.db.models import Q
from django.conf import settings
from .models import Nmapscan, NmapAssets
from .nmapops import execute_nmap_scan_db
import json

localinteractionurl = settings.LOCAL_INTERACTION_URL

@login_required
def overview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    assets = NmapAssets.objects.order_by('-id')[:5]
    scans = Nmapscan.objects.order_by('-id')[:5]
    return render(
        request,
        'overview.html',
        {
            'title':'NMAP Overview',
            'year':datetime.now().year,
            'assets':assets,
            'scans':scans,
            'chatcontext':"Shows Assets form the NMAP scans aswell as the nmap scans witch where run." 
        }
    )

@login_required
def scan(request):
    if request.method == 'POST':
        ip = request.POST.get('ip')
        parameters = request.POST.get('parameters')

        execute_nmap_scan_db(ip, parameters)

        assets = NmapAssets.objects.order_by('-id')[:5]
        scans = Nmapscan.objects.order_by('-id')[:5]

        return render(
            request,
            'overview.html',
            {
                'title':'NMAP Overview',
                'year':datetime.now().year,
                'assets':assets,
                'scans':scans,
                'chatcontext':"Shows Assets form the NMAP scans aswell as the nmap scans witch where run." 
            }
        )

    else:
        """Renders the about page."""
        assert isinstance(request, HttpRequest)
        return render(
            request,
            'nmapscan.html',
            {
                'title':'NMAP Overview',
                'year':datetime.now().year,
                'chatcontext':"Shows a form with the input options IP/IP-Range aswell as the Parameters for a NMAP Scan. Parameters dont require nmap in the beginning."

            }
    )


@login_required
def scansoverview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    query = request.GET.get("search")
    if query == None or query == "":
        scans = Nmapscan.objects.order_by('-id')
    else:
        scans = Nmapscan.objects.filter(Q(data__icontains=query) | Q(ip__icontains=query) | Q(parameters__icontains=query) | Q(created_at__icontains=query)).order_by('-id')
    paginator = Paginator(scans, 5)
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the appropriate page of blog posts
    return render(
        request,
        'scansoverview.html',
        {
            'title':'NMAP Scans Overview',
            'year':datetime.now().year,
            'scans':page_obj
        }
    )


@login_required
def scanview(request, id):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    scans = Nmapscan.objects.get(id=id)
    return render(
        request,
        'scanview.html',
        {
            'title':'NMAP Scans View',
            'year':datetime.now().year,
            'scans':scans,
            'chatcontext':"Report about a NMAP Scan. Displayed Scan-Date, Target(-Range) and Scan-Parameters." + "The following scan arameters where used: " + scans.parameters + ". The NMAP Scan Result is: " + scans.data
        }
    )


@login_required
def nmapassetsoverview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    query = request.GET.get("search")
    if query == None or query == "":
        assets = NmapAssets.objects.order_by('-id')
    else:
        assets = NmapAssets.objects.filter(Q(hostname__icontains=query) | Q(ip_address__icontains=query)).order_by('-id')

    paginator = Paginator(assets, 5)
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the appropriate page of blog posts
    return render(
        request,
        'nmapassetsoverview.html',
        {
            'title':'NMAP Assets Overview',
            'year':datetime.now().year,
            'assets':page_obj
        }
    )

@login_required
def nmapassetview(request, id):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    assets = NmapAssets.objects.get(id=id)
    return render(
        request,
        'nmapassetview.html',
        {
            'title':'NMAP Scans View',
            'year':datetime.now().year,
            'assets':assets,
            'chatcontext':f"Report about a Asset from a NMAP Scan. The Asset data is: {assets.json_data}."
        }
    )