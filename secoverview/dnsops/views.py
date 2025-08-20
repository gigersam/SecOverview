from django.shortcuts import render
from django.http import HttpRequest
from django.core.paginator import Paginator
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .dnsops import enumerate_dns_records, generate_variants

@login_required
def dnsoverview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        domain = request.POST.get('domain')
        subdomain = bool(request.POST.get('subdomain'))
        obfuscation = bool(request.POST.get('obfuscation'))

        if subdomain:
            subdomain_results = enumerate_dns_records(domain=domain)
        else:
            subdomain_results = ""
        
        if obfuscation:
            obfuscation_results = generate_variants(domain=domain)
        else:
            obfuscation_results = ""

        return render(
            request,
            'dnsoverview.html',
            {
                'title':'DNS Query',
                'year':datetime.now().year,
                'subdomain_results':subdomain_results,
                'obfuscation': obfuscation_results,
                'chatcontext':"This page helps to create a dns querry. Enter IP or FQDN witch needs to be checkt. The following Results where discoverd in the latest scan: " + str(subdomain_results) 
            }
        )

    else:
        return render(
            request,
            'dnsoverview.html',
            {
                'title':'DNS Query',
                'year':datetime.now().year,
                'subdomain_results':"",
                'obfuscation': "",
                'chatcontext':"This page helps to create a dns querry. Enter IP or FQDN witch needs to be checkt."
            }
        )

