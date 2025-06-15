from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
from .cve_ops import get_load_all_cve_data
from .models import CveItem

@login_required
def cve_view(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    query = request.GET.get("search")
    if query == None or query == "":
        cves = CveItem.objects.order_by('-cve_id')
    else:
        cves = CveItem.objects.filter(Q(cve_id__icontains=query) | Q(source_identifier__icontains=query) | Q(vuln_status__icontains=query) | Q(descriptions__icontains=query) | Q(metrics__icontains=query) | Q(weaknesses__icontains=query) | Q(references__icontains=query)).order_by('-cve_id')
    paginator = Paginator(cves, 5)
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the appropriate page of blog posts
    return render(
        request,
        'cve_view.html',
        {
            'title':'CVE',
            'year':datetime.now().year,
            'cves':page_obj
        }
    )

@login_required
def get_cve_data(request):
    assert isinstance(request, HttpRequest)
    get_load_all_cve_data()
    return redirect('cve_view')

@login_required
def cve_details(request, id):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    cve = CveItem.objects.get(cve_id=id)
    return render(
        request,
        'cve_details.html',
        {
            'title':'CVE Details',
            'year':datetime.now().year,
            'cve':cve
        }
    )