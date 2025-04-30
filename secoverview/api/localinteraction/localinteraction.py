import requests
from django.conf import settings
from .config import CREDENTIALS

localinteractionurl = settings.LOCAL_INTERACTION_URL

def local_api_request(api_url, data):
    token_url = localinteractionurl + "/api/token"  # Adjust this to match your API
    credentials = CREDENTIALS

    try:
        # Make the request to get the token
        response = requests.post(token_url, json=credentials)
        response.raise_for_status()  # Raise error if request fails

        # Extract access token
        access_token = response.json().get("access")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(api_url, headers=headers, json=data)
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return (f"Error obtaining access token: {e}")
    
def local_api_request_get(api_url):
    token_url = localinteractionurl + "/api/token"  # Adjust this to match your API
    credentials = CREDENTIALS

    try:
        # Make the request to get the token
        response = requests.post(token_url, json=credentials)
        response.raise_for_status()  # Raise error if request fails

        # Extract access token
        access_token = response.json().get("access")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(api_url, headers=headers)
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return (f"Error obtaining access token: {e}")