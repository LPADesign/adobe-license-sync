import requests
import json
import math
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from elasticsearch import Elasticsearch

# Elastic config
cloud_id = 'lpa_bimbeats:dXMtd2VzdC0yLmF3cy5mb3VuZC5pbyQzM2RiMTFkZTI2NzA0MjVmYTA0ZWJhYTU4OTY4NWFkMyQzNDFkNWI3ODFkZjM0ZTg1OWZkZTA1OTQzYmM4NWM1ZA=='
api_key_id = 'AxQnmocBF3N7DMc-nPf1'
api_key = 'mJXhw019TT2SAbWvgpzwwQ'
es = Elasticsearch(cloud_id=cloud_id, api_key=(api_key_id, api_key))

# Adobe config
adobeOrgID = 'A2AE196C5C7874E00A495E82@AdobeOrg'
adobeClientID = '1298434b2be941218b2db69fac65222c'
adobeClientSecret = 'p8e-mBN25uTNVDZ_yhnK89Wt2LCFb5viTFuA'
adobeScopes = 'openid, AdobeID, user_management_sdk'  # use your actual scopes

def retrieveToken():
    url = 'https://ims-na1.adobelogin.com/ims/token/v3'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_id': adobeClientID,
        'client_secret': adobeClientSecret,
        'grant_type': 'client_credentials',
        'scope': adobeScopes
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to retrieve token: {response.status_code} {response.text}")

def getAdobeUsers():
    token = retrieveToken()
    headers = {
        'Authorization': f"Bearer {token}",
        'x-api-key': adobeClientID,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    productProfile = 'Default Creative Cloud All Apps - Pro Edition configuration'
    productProfileUrl = productProfile.replace(' ', '%20')
    url = f'https://usermanagement.adobe.io/v2/usermanagement/users/{adobeOrgID}/0/{productProfileUrl}'
    response = requests.get(url, headers=headers)

    if response.status_code == 429:
        wait_retry(response)
        response = requests.get(url, headers=headers)

    adobeUsers = []
    readable = response.json()
    for user in readable.get('users', []):
        username = user['username'].split('@')[0].lower()
        adobeUsers.append(f"LPA\\{username}")

    print(f"Total Adobe users: {len(adobeUsers)}")
    getLastUsage(adobeUsers, productProfile)

def wait_retry(response):
    wait_time = int(response.headers.get('retry-after', 60)) + 60
    next_time = datetime.now() + timedelta(seconds=wait_time)
    print(f"Rate-limited. Retrying at {next_time.strftime('%H:%M')}...")
    time.sleep(wait_time)

def getLastUsage(users, productProfile):
    stale_users = []
    for user in users:
        email = user.split('\\')[1]
        query = {
            "query": {
                "bool": {
                    "must": [{"match_phrase": {"user.name.keyword": user}}],
                    "should": [
                        {"match_phrase": {"process.name.keyword": "Photoshop.exe"}},
                        {"match_phrase": {"process.name.keyword": "Illustrator.exe"}},
                        {"match_phrase": {"process.name.keyword": "InDesign.exe"}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": 1,
            "sort": [{"@timestamp": {"order": "desc"}}]
        }

        results = es.search(index="beat-metricbeat-7.7.0*", body=query)
        hits = results.get('hits', {}).get('hits', [])

        if hits:
            last_used = datetime.strptime(hits[0]['_source']['@timestamp'].split('T')[0], '%Y-%m-%d')
            if last_used < datetime.today() - timedelta(weeks=2):
                stale_users.append(email)
                print(f"{user} last used Adobe on {last_used} — MARKED FOR REMOVAL")
            else:
                print(f"{user} last used Adobe on {last_used}")
        else:
            print(f"{user} has no usage logs — MARKED FOR REMOVAL")
            stale_users.append(email)

    if stale_users:
        print(f"🚫 Removing {len(stale_users)} users...")
        removeAdobeUsers(stale_users, productProfile)
    else:
        print("✅ No users need to be removed.")

def removeAdobeUsers(user_list, productProfile):
    token = retrieveToken()
    headers = {
        'Authorization': f"Bearer {token}",
        'x-api-key': adobeClientID,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    url = f'https://usermanagement.adobe.io/v2/usermanagement/action/{adobeOrgID}'

    for user in user_list:
        user_email = f"{user}@lpadesignstudios.com"
        body = [{
            "user": user_email,
            "requestID": "autoRemoveInactive",
            "do": [{"remove": "all"}]
        }]
        response = requests.post(url, headers=headers, data=json.dumps(body))

        if response.status_code == 429:
            wait_retry(response)
            response = requests.post(url, headers=headers, data=json.dumps(body))

        try:
            result = response.json()
            if result.get('result') == 'success':
                print(f"✅ Removed Adobe access for {user_email}")
            else:
                print(f"⚠️ Failed to remove {user_email}: {result}")
        except:
            print(f"⚠️ Error parsing response for {user_email}: {response.text}")

# Run it
getAdobeUsers()
