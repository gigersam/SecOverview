from .models import RansomwareliveVictim, RansomwareliveGroupsGroup, RansomwareliveGroupsLocation, RansomwareliveGroupsProfile
import requests

def fetch_ransomwarelive_victims():
    try:
        response = requests.get('https://data.ransomware.live/victims.json')
        if response.status_code == 200:
            data = response.json()
            for victim in data:
                RansomwareliveVictim.add_post(victim)
        return True
    except Exception as e:
        print(f"Error fetching ransomware live victims: {e}")
        return False
    
def fetch_ransomwarelive_groups():
    try:
        response = requests.get('https://data.ransomware.live/groups.json')
        if response.status_code == 200:
            data = response.json()
            for group_data in data:
                group, created = RansomwareliveGroupsGroup.objects.get_or_create(name=group_data['name'])
                for location in group_data.get('locations', []):
                    RansomwareliveGroupsLocation.objects.get_or_create(fqdn=location['fqdn'], group=group)
                for profile in group_data.get('profile', []):
                    RansomwareliveGroupsProfile.objects.get_or_create(link=profile, group=group)
        return True
    except Exception as e:
        print(f"Error fetching ransomware live groups: {e}")
        return False