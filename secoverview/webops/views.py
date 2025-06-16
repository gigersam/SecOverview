from django.shortcuts import render
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .webops.web_headers import check_security_headers
from .webops.crt_sh_ops import query_crtsh
from .webops.web_tech_fingerprinting import analyze_technologies
from .models import CRTSHResult, WebTechFingerprinting_Results

@login_required
def web_overview(request):
    """View to display RSS feed data"""
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        domain = request.POST.get('domain')
        headers = check_security_headers(domain)
        crt_result = CRTSHResult.objects.filter(domain=query_crtsh(domain))
        webtechfingerprint = WebTechFingerprinting_Results.objects.filter(domain=analyze_technologies(domain))
        return render(
            request, 
            "web_overview.html", 
            {
                'title':'Web Ops Overview',
                'year':datetime.now().year,
                'domain':domain, 
                'webheaders':headers,
                'crt_result':crt_result,
                'webtechfingerprint':webtechfingerprint,
                'chatcontext':"This page "
            })
    else:
        return render(
            request, 
            "web_overview.html", 
            {
                'title':'Web Ops Overview',
                'year':datetime.now().year,
                'domain':None,
                'webheaders':None,
                'crt_scan_result':None,
                'webtechfingerprint':None,
                'chatcontext':"This page "
            })
