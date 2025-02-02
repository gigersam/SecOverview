import requests
from config import CREDENTIALS

def local_api_request(api_url, data):
    token_url = "http://127.0.0.1:8000/api/token"  # Adjust this to match your API
    credentials = CREDENTIALS

    try:
        # Make the request to get the token
        print(token_url)
        response = requests.post(token_url, json=credentials)
        response.raise_for_status()  # Raise error if request fails

        # Extract access token
        access_token = response.json().get("access")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(api_url, headers=headers, json=data)
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return (f"Error obtaining access token: {e}")