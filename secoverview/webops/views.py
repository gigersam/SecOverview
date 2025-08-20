from django.shortcuts import render
from django.http import HttpRequest
from django.core import serializers
from django.contrib.auth.decorators import login_required
from datetime import datetime
from chat.clearnebel_agent_builder import clearnebel
from .webops.web_headers import check_security_headers
from .webops.crt_sh_ops import query_crtsh
from .webops.web_tech_fingerprinting import analyze_technologies
from .models import CRTSHResult, WebTechFingerprinting_Results, WebOpsScan
from .serializers import WebHeaderCheckSerializer

@login_required
def web_overview(request):
    """View to display RSS feed data"""
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        domain = request.POST.get('domain')
        action = request.POST.get('action')
        headers = check_security_headers(domain)
        crt_scan = query_crtsh(domain)
        crt_result = CRTSHResult.objects.filter(domain=crt_scan)
        webtechfingerprint_scan = analyze_technologies(domain)
        webtechfingerprint = WebTechFingerprinting_Results.objects.filter(domain=webtechfingerprint_scan)
        
        if action == "checkllm":
            if clearnebel != "":
                llmresponse = clearnebel.get_response_as_html(f"Summarize and point out the most relevant key points regarding security aspects: {WebHeaderCheckSerializer(headers).data}, {serializers.serialize('json', crt_result)}, {serializers.serialize('json', webtechfingerprint)}")
            else:
                llmresponse = None
        else:
            llmresponse = None
        
        WebOpsScan.objects.create(domain=domain, webtech=webtechfingerprint_scan, crtshscan=crt_scan, webheader=headers, llmsummary=llmresponse)

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
                'llm':llmresponse,
                'chatcontext':f"This page show the following data: {domain} - {headers} - {crt_result} - {webtechfingerprint} "
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
                'llm':None,
                'chatcontext':"This page allows to querry a domain for its web technologies, cert subdomains history and its http security headers."
            })
