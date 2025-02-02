from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from ransomwarelive.models import RansomwareliveVictim, RansomwareliveGroupsGroup, RansomwareliveGroupsLocation, RansomwareliveGroupsProfile
import requests
import nmap

@api_view(['POST'])
def logout_view(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logged out successfully."})
    except Exception as e:
        return Response({"error": str(e)}, status=400)

# Protected API view
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": f"Hello, {request.user.username}! This is a protected API."})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test():
    return Response({"message": f"Hello, testsite! This is a protected API."})

@api_view(['GET'])
#@permission_classes([IsAuthenticated])
def fetch_victims(request):
    response = requests.get('https://data.ransomware.live/victims.json')
    if response.status_code == 200:
        data = response.json()
        for victim in data:
            RansomwareliveVictim.add_post(victim)
        return Response({'message': 'Victims data fetched and added successfully'}, status=200)
    return Response({'error': 'Failed to fetch victims data'}, status=500)

@api_view(['GET'])
#@permission_classes([IsAuthenticated])
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


    

