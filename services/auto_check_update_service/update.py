import os
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URI = os.getenv('APISERVERURL')

def get_token():
    url = BASE_URI + "/api/token"
    CREDENTIALS = {
        "username": os.getenv('CREDENTIALSUSERNAME'),
        "password": os.getenv('CREDENTIALSPASSWORD')
    }
    response = requests.post(url, json=CREDENTIALS)
    if response.status_code == 200:
        tokens = response.json()
        return tokens.get("access"), tokens.get("refresh")
    else:
        logging.info(f"GET_TOKEN: Failed to get token: {response.text}")
        return None, None
    
def refresh_token(refresh_token):
    url = BASE_URI + "/api/token/refresh"
    response = requests.post(url, data={
        'refresh': refresh_token,
    })
    if response.status_code == 200:
        tokens = response.json()
        return tokens.get("access"), refresh_token
    else:
        logging.info(f"REFRESH_TOKEN: Failed to refresh token: {response.text}")
        return None, None
    
def token_management(token_set, last_update, refresh_token_val_in, access_token_in):
    now = datetime.now()
    if token_set == False or refresh_token_val_in is None:
        access_token, refresh_token_val  = get_token()
        if access_token != None or refresh_token_val_in != None:
            token_set = True
            return access_token, refresh_token_val, token_set
        else:
            return access_token_in, refresh_token_val_in, token_set
    elif now - last_update > timedelta(days=6, hours=23) or access_token_in is None:
        access_token, refresh_token_val = refresh_token(refresh_token_val_in)
        if access_token != None or refresh_token_val != None:
            return access_token, refresh_token_val, token_set
        else:
            return access_token_in, refresh_token_val_in, token_set
    else:
        return access_token_in, refresh_token_val_in, token_set

def update_assets(last_update_assets, update_cycle_assets, headers):
    # Gather all Assets an
    if last_update_assets is None or (datetime.now() - last_update_assets) > timedelta(minutes=update_cycle_assets):
        url = BASE_URI + "/api/assets/gather/all"
        response = requests.get(url, headers=headers)
        if response == 200:
            logging.info(f"ASSETS: Succsefully updated all assets.")
            last_update_assets = datetime.now()
            return last_update_assets
        else:
            logging.info(f"ASSETS: Failed to update all assets. Response code: {response.status_code}")
            return last_update_assets
    else:
        return last_update_assets


def update_ransomware(last_update_ransomware, update_cycle_ransomwarelive, headers):
    # Gather ransomwarelive data
    if last_update_ransomware is None or (datetime.now() - last_update_ransomware) > timedelta(days=update_cycle_ransomwarelive):
        url = BASE_URI + "/api/ransomwarelive/groups/fetch"
        response = requests.get(url, headers=headers)
        if response == 200:
            logging.info(f"ASSETS: Succsefully updated all ransomwarelive groups.")
        else:
            logging.info(f"ASSETS: Failed to update all ransomwarelive groups. Response code: {response.status_code}")
            return last_update_ransomware
        url = BASE_URI + "/api/ransomwarelive/victims/fetch"
        response = requests.get(url, headers=headers)
        if response == 200:
            logging.info(f"ASSETS: Succsefully updated all ransomwarelive victims.")
            last_update_ransomware = datetime.now()
            return last_update_ransomware
        else:
            logging.info(f"ASSETS: Failed to update all ransomwarelive victims. Response code: {response.status_code}")
            return last_update_ransomware
    else:
        return last_update_ransomware

def update_rss_feed(last_update_rss_feed, update_cycle_rss_feed, headers):
    if last_update_rss_feed is None or (datetime.now() - last_update_rss_feed) > timedelta(days=update_cycle_rss_feed):
        url = BASE_URI + "/api/assets/gather/all"
        response = requests.get(url, headers=headers)
        if response == 200:
            logging.info(f"RSSFEED: Succsefully updated RSS Feed.")
            last_update_rss_feed = datetime.now()
            return last_update_rss_feed
        else:
            logging.info(f"RSSFEED: Failed to update RSS Feed. Response code: {response.status_code}")
            return last_update_rss_feed
    else:
        return last_update_rss_feed
    
if __name__ == '__main__':
    token_set = False
    last_update = datetime.now()
    access_token = None
    refresh_token_val = None
    last_update_assets = None
    last_update_ransomware = None
    last_update_rss_feed = None
    update_cycle_assets = int(os.getenv('UPDATE_CYCLE_ASSETS'))
    update_cycle_ransomwarelive = int(os.getenv('UPDATE_CYCLE_RANSOMWARELIVE'))
    update_cycle_rss_feed = int(os.getenv('UPDATE_CYCLE_RSS_FEED'))
    
    while True:
        access_token, refresh_token_val, token_set = token_management(token_set=token_set, last_update=last_update, refresh_token_val_in=refresh_token_val, access_token_in=access_token)
        if access_token != None:
            headers = {"Authorization": f"Bearer {access_token}"}
            last_update_assets = update_assets(last_update_assets=last_update_assets, update_cycle_assets=update_cycle_assets, headers=headers)
            last_update_ransomware = update_ransomware(last_update_ransomware=last_update_ransomware, update_cycle_ransomwarelive=update_cycle_ransomwarelive, headers=headers)
            last_update_rss_feed = update_ransomware(last_update_rss_feed=last_update_rss_feed, update_cycle_rss_feed=update_cycle_rss_feed, headers=headers)
            

