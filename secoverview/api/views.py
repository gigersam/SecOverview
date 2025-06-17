from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from assets.assetsoperations import gather_all
from dnsops.dnsops import enumerate_dns_records
from rssapp.views import fetch_rss_feed
from ransomwarelive.models import RansomwareliveVictim, RansomwareliveGroupsGroup, RansomwareliveGroupsLocation, RansomwareliveGroupsProfile
from mlnids.models import NetworkFlow, RfPrediction
from cvedata.cve_ops import get_load_all_cve_data
from webops.models import CRTSHResult, WebTechFingerprinting_Results
from webops.webops.crt_sh_ops import query_crtsh
from webops.webops.web_headers import check_security_headers
from webops.webops.web_tech_fingerprinting import analyze_technologies
from ipcheck.views import get_external_ip_info
from .serializers import CRTSHResultSerializer, WebHeaderCheckSerializer, WebTechFingerprinting_ResultsSerializer
import requests
import nmap
import csv
import io

@api_view(['POST'])
def logout_view(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logged out successfully."})
    except Exception as e:
        return Response({"error": str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test():
    return Response({"message": f"Hello, testsite! This is a protected API."})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_victims(request):
    response = requests.get('https://data.ransomware.live/victims.json')
    if response.status_code == 200:
        data = response.json()
        for victim in data:
            RansomwareliveVictim.add_post(victim)
        return Response({'message': 'Victims data fetched and added successfully'}, status=200)
    return Response({'error': 'Failed to fetch victims data'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_groups(request):
    response = requests.get('https://data.ransomware.live/groups.json')
    if response.status_code == 200:
        data = response.json()
        for group_data in data:
            group, created = RansomwareliveGroupsGroup.objects.get_or_create(name=group_data['name'])
            for location in group_data.get('locations', []):
                RansomwareliveGroupsLocation.objects.get_or_create(fqdn=location['fqdn'], group=group)
            for profile in group_data.get('profile', []):
                RansomwareliveGroupsProfile.objects.get_or_create(link=profile, group=group)
        return Response({'message': 'Groups data fetched and added successfully'}, status=200)
    return Response({'error': 'Failed to fetch groups data'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nmap_scan(request):
    # Ensure request data is JSON
    if not isinstance(request.data, dict):
        return Response({'error': 'Invalid JSON'}, status=400)
    
    # Access JSON data
    ip = request.data.get('ip', 'Guest')
    parameters = request.data.get('parameters', None)

    scanner = nmap.PortScanner()
    try:
        # Scan the subnet with service detection
        scanner.scan(hosts=ip, arguments=parameters)
        combined = []
        for host in scanner.all_hosts():
            combined.append(scanner[host])

        return Response(combined, status=200)

    except Exception as e:
        return Response(e, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mlnids_upload_csv(request):
    file = request.FILES.get('file')
    
    if not file:
        return Response({'error': 'No file provided'}, status=400)
    
    if not file.name.endswith('.csv'):
        return Response({'error': 'Only CSV files are supported'}, status=400)

    try:
        decoded_file = file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        print(reader)
        entries = []
        for row in reader:
            prediction_label = row.pop("rf_prediction", "Unknown")
            prediction, _ = RfPrediction.objects.get_or_create(label=prediction_label)
            print(prediction)
            # Boolean conversion
            anomaly_flag = row.get("if_is_anomaly", "False") in ["True", "true", "1"]

            flow = NetworkFlow(
                rf_prediction=prediction,
                rf_confidence=row.pop("rf_confidence", 0),
                if_anomaly_score=row.pop("if_anomaly_score", 0),
                if_is_anomaly=anomaly_flag
            )

            for key, value in row.items():
                print(f"Setting {key} to {value}")
                if hasattr(flow, key):
                    # Try to cast to appropriate type if needed
                    setattr(flow, key, value)
            
            try:
                flow.save()
            except Exception as e:
                print(f"Error saving flow: {e}")

            entries.append(flow)
        print(f"{entries}")
        NetworkFlow.objects.bulk_create(entries, ignore_conflicts=True)
        return Response({'message': f'{len(entries)} records uploaded.'}, status=201)

    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assets_gather_all(request):
    try:
        # Call the function you want to execute
        gather_all()
        return Response({'message': 'Gather assets and detection information successfully'}, status=200)
    except Exception as e:
        return Response({f'error': 'Failed gather assets and detection information'}, status=500)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rss_feed_update(request):
    try:
        # Call the function you want to execute
        fetch_rss_feed()
        return Response({'message': 'Gather RSS Feeds successfully'}, status=200)
    except Exception as e:
        return Response({f'error': 'Failed gather RSS Feed'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cve_get_daily(request):
    try:
        # Call the function you want to execute
        get_load_all_cve_data()
        return Response({'message': 'Gather CVE successfully'}, status=200)
    except Exception as e:
        return Response({f'error': 'Failed gather CVE'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_crtsh_get(request):
    domain = request.GET.get('q')
    print(f'query domain: {domain}')
    # Check if a query parameter is provided in the URL
    if not domain:
        return Response({'message': 'No query parameter provided'}, status=400)
    
    results = CRTSHResult.objects.filter(domain=query_crtsh(domain))
    serializer = CRTSHResultSerializer(results, many=True)
    return Response(serializer.data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_webheaders_get(request):
    domain = request.GET.get('q')
    print(f'query domain: {domain}')
    # Check if a query parameter is provided in the URL
    if not domain:
        return Response({'message': 'No query parameter provided'}, status=400)
    
    results = check_security_headers(domain)
    serializer = WebHeaderCheckSerializer(results, many=False)
    return Response(serializer.data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_webfingerprinting_get(request):
    domain = request.GET.get('q')
    print(f'query domain: {domain}')
    # Check if a query parameter is provided in the URL
    if not domain:
        return Response({'message': 'No query parameter provided'}, status=400)
    
    results = WebTechFingerprinting_Results.objects.filter(domain=analyze_technologies(domain))
    serializer = WebTechFingerprinting_ResultsSerializer(results, many=True)
    return Response(serializer.data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_weball_get(request):
    domain = request.GET.get('q')
    print(f'query domain: {domain}')
    # Check if a query parameter is provided in the URL
    if not domain:
        return Response({'message': 'No query parameter provided'}, status=400)
    
    results_certinfo = CRTSHResult.objects.filter(domain=query_crtsh(domain))
    results_securityheaders = check_security_headers(domain)
    results_webtechfingerprinting = WebTechFingerprinting_Results.objects.filter(domain=analyze_technologies(domain))
    
    data = {
        'certinfo': CRTSHResultSerializer(results_certinfo, many=True).data,
        'securityheaders': WebHeaderCheckSerializer(results_securityheaders, many=False).data,
        'webtechfingerprinting': WebTechFingerprinting_ResultsSerializer(results_webtechfingerprinting, many=True).data
    }

    return Response(data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dns_enumerate(request):
    domain = request.GET.get('q')
    print(f'query domain: {domain}')
    # Check if a query parameter is provided in the URL
    if not domain:
        return Response({'message': 'No query parameter provided'}, status=400)
    
    subdomain_results = enumerate_dns_records(domain=domain)
    return Response(subdomain_results, status=200)

@api_view(['GET'])
#@permission_classes([IsAuthenticated])
def api_ipcheck_get(request):
    ip = request.GET.get('q')
    print(f'query domain: {ip}')
    if not ip:
        return Response({'message': 'No query parameter provided'}, status=400)
    
    bgpviewdata, abuseipdb_data, misp_data  = get_external_ip_info(ip=ip)
    if not bgpviewdata == None:
        bgpviewdata = bgpviewdata['data']
    if not abuseipdb_data == None:
        abuseipdb_data = abuseipdb_data['data']

    data = {
        'bgpview': bgpviewdata,
        'abuseipdb': abuseipdb_data,
        'misp': misp_data
    }
    return Response(data, status=200)