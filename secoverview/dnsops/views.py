from django.shortcuts import render
from django.http import HttpRequest
from django.core.paginator import Paginator
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import DNSQuery, DNSRecord
import dns.resolver
import dns.zone
import dns.query

SUBDOMAIN_LIST = ["www", "mail", "ftp", "api", "blog", "dev", "test", "staging", "support", "shop"]

@login_required
def dnsoverview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        domain = request.POST.get('domain')
        results = {}
        print(domain)
        for record_type in DNSRecord.RECORD_TYPES:
            record_type = record_type[0]
            try:
                answers = dns.resolver.resolve(domain, record_type)
                print(answers)
                results[record_type] = [str(record) for record in answers]
            except:
                pass
        print(results)

        subdomain_results = {}
        subdomain_results[domain] = results
        for subdomain in SUBDOMAIN_LIST:
            full_domain = f"{subdomain}.{domain}"
            subdomain_records = {}

            for record_type in DNSRecord.RECORD_TYPES:
                record_type = record_type[0]
                try:
                    answers = dns.resolver.resolve(full_domain, record_type)
                    subdomain_records[record_type] = [str(record) for record in answers]
                except:
                    pass
            
            if subdomain_records:
                subdomain_results[full_domain] = subdomain_records

        return render(
            request,
            'dnsoverview.html',
            {
                'title':'DNS Query',
                'year':datetime.now().year,
                'subdomain_results':subdomain_results
            }
        )

    else:
        return render(
            request,
            'dnsoverview.html',
            {
                'title':'DNS Query',
                'year':datetime.now().year,
                'subdomain_results':""
            }
        )

