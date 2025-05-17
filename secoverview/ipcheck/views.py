from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.conf import settings
from .misp_client import misp_instance
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
            response = requests.get(f"https://api.bgpview.io/ip/{ip}")
            response = response.json()
            if settings.ABUSEIPDB_API_KEY != "your_api_key_here":
                abuseipdb_data = get_abuse_ip_db(ip)
            else:
                abuseipdb_data = None
            if misp_instance != None:
                misp_data = misp_instance.check_ipv4(ip)
            else:
                misp_data = None
            return render(
                request,
                'ipcheck.html',
                {
                    'title':'IP Check',
                    'year':datetime.now().year,
                    'response':response['data'],
                    'abuseipdb':abuseipdb_data['data'] if abuseipdb_data else None,
                    'misp':misp_data,
                    'chatcontext':"This page is a bgp/asn check. Input allowed IP-Address. The following Data was returned: " + str(response['data']) 
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
