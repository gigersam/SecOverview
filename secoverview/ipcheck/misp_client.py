from django.conf import settings
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MISP:
    def __init__(self, mispaddr="0.0.0.0", misp_key="", verify_ssl=False): 
        self.mispaddr = mispaddr
        self.misp_key = misp_key
        self.verify_ssl = verify_ssl
        self.headers = headers = {
            'Authorization': self.misp_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def query_misp(self, query):
        # Make the request
        url = f"https://{self.mispaddr}/attributes/restSearch"
        response = requests.post(url, headers=self.headers, json=query, verify=self.verify_ssl)
        return response

    def check_ipv4(self, ip):
        
        query = {
            "returnFormat": "json",
            "type": "ip-dst",
            "value": ip
        }

        # Make the request
        response = self.query_misp(query=query)

        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            result = result['response']
            # result is a dictionary containing "Attribute" (if matches found)
            if 'Attribute' in result and len(result['Attribute']) > 0: 
                return result['Attribute']
        else:
            return "Response:", response.text
        
if settings.MISP_API_KEY != "your_api_key_here" or settings.MISP_API_KEY != "" or settings.MISP_SERVER != "IP":
    misp_instance = MISP(
        mispaddr=settings.MISP_SERVER,
        misp_key=settings.MISP_API_KEY,
        verify_ssl=False
    )
else:
    misp_instance = None