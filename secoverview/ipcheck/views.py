from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from .misp_client import misp_instance
from .models import IpcheckMISP, IpcheckAbuseIPDB, Ipcheckbgpview
import requests
import ipaddress

def is_internal_ip(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False

def get_abuse_ip_db(ip):
    """Returns the abuse IP DB response for a given IP address."""
    url = 'https://api.abuseipdb.com/api/v2/check'
    querystring = {
        'ipAddress': ip,
        'maxAgeInDays': '90'
    }
    headers = {
        'Accept': 'application/json',
        'Key': settings.ABUSEIPDB_API_KEY
    }
    abuseipdb_response = requests.get(url, headers=headers, params=querystring)
    if abuseipdb_response.status_code == 200:
        return abuseipdb_response.json()
    else:
        return None

def get_misp_ip_data(ip):
    """Returns the MISP IP data for a given IP address."""
    url = f"https://www.misp.org/api/v2/ip/{ip}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()

@login_required
def ipcheck(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        ip = request.POST.get('ip')
        if is_internal_ip(ip) != True:
            cached_bgpview = Ipcheckbgpview.objects.filter(ip=ip).order_by('-created_at').first()
            if cached_bgpview and cached_bgpview.created_at > timezone.now() - timedelta(hours=1):
                bgpviewdata = cached_bgpview.data
            else:
                response = requests.get(f"https://api.bgpview.io/ip/{ip}")
                bgpviewdata = response.json()
                Ipcheckbgpview.objects.create(ip=ip, data=bgpviewdata)
            
            if settings.ABUSEIPDB_API_KEY != "your_api_key_here":
                cached_abuse_ip_db = IpcheckAbuseIPDB.objects.filter(ip=ip).order_by('-created_at').first()
                if cached_abuse_ip_db and cached_abuse_ip_db.created_at > timezone.now() - timedelta(hours=1):
                    abuseipdb_data = cached_abuse_ip_db.data
                else:
                    abuseipdb_data = get_abuse_ip_db(ip)
                    if abuseipdb_data:
                        IpcheckAbuseIPDB.objects.create(ip=ip, data=abuseipdb_data)
                    else:
                        abuseipdb_data = None
            else:
                abuseipdb_data = None
            if misp_instance != None or misp_instance != "none":
                cached_misp_data = IpcheckMISP.objects.filter(ip=ip).order_by('-created_at').first()
                if cached_misp_data and cached_misp_data.created_at > timezone.now() - timedelta(hours=24):
                    misp_data = cached_misp_data.data
                else:
                    misp_data = misp_instance.check_ipv4(ip)
                    if misp_data:
                        IpcheckMISP.objects.create(ip=ip, data=misp_data)
                    else:
                        IpcheckMISP.objects.create(ip=ip, data=None)
                        misp_data = None
            else:
                misp_data = None
            return render(
                request,
                'ipcheck.html',
                {
                    'title':'IP Check',
                    'year':datetime.now().year,
                    'response':bgpviewdata['data'],
                    'abuseipdb':abuseipdb_data['data'] if abuseipdb_data else None,
                    'misp':misp_data,
                    'chatcontext':"This page is a bgp/asn check. Input allowed IP-Address. The following Data was returned: " + str(bgpviewdata['data']) + ". The abuseipdb data is: " + str(abuseipdb_data['data']) + ". The MISP data is: " + str(misp_data)
                }
            )
        else:
            return render(
                request,
                'ipcheck.html',
                {
                    'title':'IP Check',
                    'year':datetime.now().year,
                    'response':f"IP is Private",
                    'abuseipdb':None,
                    'misp':None,
                    'chatcontext':"This page is a bgp/asn check. Input allowed IP-Address."
                }
            )
    else:
        return render(
            request,
            'ipcheck.html',
            {
                'title':'IP Check',
                'year':datetime.now().year,
                'response':"",
                'abuseipdb':None,
                'misp':None,
                'chatcontext':"This page is a bgp/asn check. Input allowed IP-Address."
            }
        )
