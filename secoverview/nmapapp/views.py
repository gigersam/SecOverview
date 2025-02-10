from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.db.models import Q
from .models import Nmapscan, Assets
from api.localinteraction.localinteraction import local_api_request

@login_required
def overview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    assets = Assets.objects.order_by('-id')[:5]
    scans = Nmapscan.objects.order_by('-id')[:5]
    return render(
        request,
        'overview.html',
        {
            'title':'NMAP Overview',
            'year':datetime.now().year,
            'assets':assets,
            'scans':scans
        }
    )

@login_required
def scan(request):
    if request.method == 'POST':
        ip = request.POST.get('ip')
        parameters = request.POST.get('parameters')

        api_url = "http://localhost:8000/api/nmap/scan"
        data = {"ip": ip, "parameters": parameters}
        json_data = local_api_request(api_url=api_url, data=data)
        scanconfig = Nmapscan.objects.create(data=json_data, ip=ip, parameters=parameters)

        for data_obj in json_data:
            ip_address = data_obj.get("addresses", {}).get("ipv4")
            hostnames = data_obj.get("hostnames", [])
            hostname = hostnames[0].get("name") if hostnames else ""

            Assets.objects.get_or_create(hostname=hostname, ip_address=ip_address, defaults={"added_by_scan": scanconfig})

        assets = Assets.objects.order_by('-id')[:5]
        scans = Nmapscan.objects.order_by('-id')[:5]

        return render(
            request,
            'overview.html',
            {
                'title':'NMAP Overview',
                'year':datetime.now().year,
                'assets':assets,
                'scans':scans
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
            'scans':scans
        }
    )


@login_required
def assetsoverview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    query = request.GET.get("search")
    if query == None or query == "":
        assets = Assets.objects.order_by('-id')
    else:
        assets = Assets.objects.filter(Q(hostname__icontains=query) | Q(ip_address__icontains=query)).order_by('-id')

    paginator = Paginator(assets, 5)
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the appropriate page of blog posts
    return render(
        request,
        'assetsoverview.html',
        {
            'title':'NMAP Assets Overview',
            'year':datetime.now().year,
            'assets':page_obj
        }
    )

@login_required
def assetview(request, id):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    assets = Assets.objects.get(id=id)
    return render(
        request,
        'assetview.html',
        {
            'title':'NMAP Scans View',
            'year':datetime.now().year,
            'assets':assets
        }
    )