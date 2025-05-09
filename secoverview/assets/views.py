from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .assetsoperations import gather_all, gather_nmap_assets_infos, gather_mlnids_assets_info
from .models import ComputeAssets, ComputeAssetsNetworkPorts, ComputeAssetsNetworkDetection

@login_required
def assetsoverview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        if request.POST.get('update_action') == 'updateall':
            gather_all()
        elif request.POST.get('update_action') == 'updateassets':
            gather_nmap_assets_infos()
        elif request.POST.get('update_action') == 'updatedetection':
            gather_mlnids_assets_info()

    query = request.GET.get("search")
    if query == None or query == "":
        assets = ComputeAssets.objects.order_by('-id')
    else:
        assets = ComputeAssets.objects.filter(Q(hostname__icontains=query) | Q(ip_address__icontains=query) | Q(description__icontains=query) | Q(asset_classification__icontains=query) | Q(threat_level__icontains=query)).order_by('-id')
    paginator = Paginator(assets, 5)
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the appropriate page of blog posts

    return render(
        request,
        'assetsoverview.html',
        {
            'title':'Assets',
            'year':datetime.now().year,
            'chatcontext':"Shows all assets with the Information Hostname, IP-Address, Description, Threat Level. There is also the option to update the Detction and/or Assets.",
            'assets':page_obj
        }
    )

@login_required
def assetview(request, id):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    asset = ComputeAssets.objects.get(id=id)
    ports = ComputeAssetsNetworkPorts.objects.filter(asset=asset)
    network_detection = ComputeAssetsNetworkDetection.objects.filter(compute_assets=asset)
    contextstring = f"This Asset {(asset.context_string() if asset != None else 'No information available')} and the following ports detected: {ports} and the following network detections: {network_detection}"
    return render(
        request,
        'assetview.html',
        {
            'title':'Asset View',
            'year':datetime.now().year,
            'asset':asset,
            'ports':ports,
            'network_detection':network_detection,
            'chatcontext':contextstring,
        }
    )