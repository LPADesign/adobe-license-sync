#######################################################################################################
#######################################################################################################
#python script to pull list of users from adobe licenses and lookup in elastic cloud to find last usage
#if greater than 2-weeks since last usage, remove access using adobe api
#######################################################################################################
#######################################################################################################
from elasticsearch import Elasticsearch, helpers
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import requests, json, math, time, jwt, base64

cloud_id = '<CLOUDID>'
api_key_id = '<APIKEYID>'
api_key = '<APIKEY>'
es = Elasticsearch(
    cloud_id=cloud_id,
    api_key=(api_key_id, api_key),
)


adobeOrgID = '<AdobeOrgID>'
adobeClientID = '<AdobeClientID>'

def retrieveToken(validMinutes):
    now = datetime.now()
    now = now + timedelta(minutes=validMinutes)
    now = now.timestamp()
    now = math.ceil(now)

    adobePrivateKey = """<PRIVATEKEY>"""


    jwtPayload = {
        "exp":now,
        "iss":"<ISSID>",
        "sub":"<SUBID>",
        "https://ims-na1.adobelogin.com/s/ent_user_sdk": True,
        "aud":"https://ims-na1.adobelogin.com/c/<ADOBECLIENTID>"
    }

    encodedJWT = jwt.encode(jwtPayload,adobePrivateKey,algorithm='RS256')
    adobeClientSecret = '<ADOBECLIENTSECRET>'
    url = 'https://ims-na1.adobelogin.com/ims/exchange/jwt'

    parameters = {
        'client_id': adobeClientID,
        'client_secret': adobeClientSecret,
        'jwt_token': encodedJWT
    }
    apirequest = requests.post(url, params=parameters)
    readable = json.loads(apirequest.content.decode('utf-8'))
    return readable['access_token']

def getAdobeUsers():
    adobeAPIToken = retrieveToken(90)
    adobeHeaders = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
        'x-api-key': adobeClientID,
        'Authorization': "Bearer " + adobeAPIToken
    }

    productProfile = 'Default Creative Cloud All Apps - Pro Edition configuration'
    productProfile = productProfile.replace(' ','%20')
    url = 'https://usermanagement.adobe.io/v2/usermanagement/users/'+adobeOrgID+'/0/'+productProfile
    apirequest = requests.get(url, headers=adobeHeaders)
    adobeUsers = []
    
    if str(apirequest.status_code) == '429':
        now = datetime.now()
        timeToWaitSeconds = int(apirequest.headers['retry-after'])
        timeToWaitSeconds = timeToWaitSeconds + 60
        timeToWait = int(apirequest.headers['retry-after']) / 60
        timeAllowed = now + timedelta(minutes=timeToWait)
        timeAllowed = timeAllowed.strftime("%H:%M")

        print('Response code: ' + str(apirequest.status_code) + ', ' + apirequest.reason)
        print('Must wait ' + str(math.ceil(timeToWait)) + ' minutes to make another API call.')
        print('Next call can be made at '+str(timeAllowed))
        print('Sleeping until the next call can be made...')
        time.sleep(timeToWaitSeconds)
        print('Starting the next call now...')
        apirequest = requests.get(url, headers=adobeHeaders)
        readable = json.loads(apirequest.content.decode('utf-8'))

        for user in readable['users']:
            username = user['username']
            username = username.split('@')
            username = username[0]
            username = username.lower()
            domainUsername = 'LPA\\'+username
            email = user['email']
            userStatus = user['status']
            adobeUsers.append(domainUsername)

        print('Total number of users to check: '+str(len(adobeUsers)))
        getLastUsage(adobeUsers, productProfile)


    else:
        readable = json.loads(apirequest.content.decode('utf-8'))
        
        for user in readable['users']:
            username = user['username']
            username = username.split('@')
            username = username[0]
            username = username.lower()
            domainUsername = 'LPA\\'+username
            email = user['email']
            userStatus = user['status']
            adobeUsers.append(domainUsername)

        print('Total number of users to check: '+str(len(adobeUsers)))
        getLastUsage(adobeUsers, productProfile)

def getLastUsage(users, productProfile):
    useremails = []
    count = 1

    for user in users:
        email = user.split('\\')
        email = email[1]
        
        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match_phrase": {
                                "user.name.keyword": user
                            }
                        }
                    ],
                    "should": [
                        {
                            "match_phrase": {
                                "process.name.keyword": "Photoshop.exe"
                            }
                        },
                        {
                            "match_phrase": {
                                "process.name.keyword": "Illustrator.exe"
                            }
                        },
                        {
                            "match_phrase": {
                                "process.name.keyword": "InDesign.exe"
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": 1,
            "sort": [{
                "@timestamp": {
                    "order": "desc"
                }
            }
            ]
        }

        results = es.search(index="beat-metricbeat-7.7.0*",body=query_body)
        all_results = results['hits']['hits']

        for result in enumerate(all_results):
            username = result[1]['_source']['user']['name']
            timestamp = result[1]['_source']['@timestamp']
            timestamp = timestamp.split("T")
            timestamp = timestamp[0]
            timestamp = datetime.strptime(timestamp, "%Y-%m-%d")
            process = result[1]['_source']['process']['name']
            current_date = datetime.today()
            threshhold = current_date - relativedelta(weeks=2)
            print(user + " last accessed at " + str(timestamp))
            print("User #"+str(count)+"\r")
            count = count + 1
            
            if timestamp < threshhold:  
                useremails.append(email)
                
            else:
                print("User " + user + " Adobe access still in use.")
                
    
    if len(useremails) == 0:
        print('Number of users checked: '+str(count-1))
        print('No users to remove!')
    else:
        print('Number of users to remove: '+str(len(useremails)))
        removeAdobeUsers(useremails, productProfile)

#def getLastUsageTEMPDELETE(user, email, productProfile):

    query_body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match_phrase": {
                            "user.name.keyword": user
                        }
                    }
                ],
                "should": [
                    {
                        "match_phrase": {
                            "process.name.keyword": "Photoshop.exe"
                        }
                    },
                    {
                        "match_phrase": {
                            "process.name.keyword": "Illustrator.exe"
                        }
                    },
                    {
                        "match_phrase": {
                            "process.name.keyword": "InDesign.exe"
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        },
        "size": 1,
        "sort": [{
            "@timestamp": {
                "order": "desc"
            }
        }
        ]
    }

    results = es.search(index="beat-metricbeat-7.7.0*",body=query_body)
    all_results = results['hits']['hits']
    useremails = []

    for result in enumerate(all_results):
        username = result[1]['_source']['user']['name']
        timestamp = result[1]['_source']['@timestamp']
        timestamp = timestamp.split("T")
        timestamp = timestamp[0]
        timestamp = datetime.strptime(timestamp, "%Y-%m-%d")
        process = result[1]['_source']['process']['name']
        current_date = datetime.today()
        threshhold = current_date - relativedelta(weeks=2)
        count = 1

        if timestamp < threshhold:
            print("User's access is stale...removing access for " + user + '...')
            if count < 11:
                useremails.append(email)
                count = count + 1
            else:
                print('Additional users will be removed next time...')
        else:
            print("User " + user + " Adobe access still in use.")

    if len(useremails) == 0:
        print('No users to remove!')

    else:
        removeAdobeUsers(useremails, productProfile)

def removeAdobeUsers(users, productProfile):
    url = 'https://usermanagement.adobe.io/v2/usermanagement/action/'+adobeOrgID
    productProfile = productProfile.replace("%20"," ")

    for user in users:
        user = user + '@lpadesignstudios.com'
    
        #parameters = \
        #[
        #    {
        #    'usergroup': productProfile,
        #    'requestID': 'RemovingStaleUser',
        #    'do': [
        #        {
        #        'remove': {
        #            'user': [
        #                "mcobb@lpadesignstudios.com"
        #            ]
        #        }
        #        }
        #    ]
        #    }
        #]
        userParameters = \
        [
            {
            "user": user,
            "requestID": "removingStaleUser",
            "do": [
                {
                "remove": "all"
                }
            ]
            }
        ]
        body = json.dumps(userParameters)
      
        adobeAPIToken = retrieveToken(90)
        adobeHeaders = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': adobeClientID,
            'Authorization': "Bearer " + adobeAPIToken
        }
        apirequest = requests.post(url, headers=adobeHeaders, data=body)
        if str(apirequest.status_code) == '429':
            now = datetime.now()
            timeToWaitSeconds = int(apirequest.headers['retry-after'])
            timeToWaitSeconds = timeToWaitSeconds + 60
            timeToWait = int(apirequest.headers['retry-after']) / 60
            timeAllowed = now + timedelta(minutes=timeToWait)
            timeAllowed = timeAllowed.strftime("%H:%M")

            print('Response code: ' + str(apirequest.status_code) + ', ' + apirequest.reason)
            print('Must wait ' + str(math.ceil(timeToWait)) + ' minutes to make another API call.')
            print('Next call can be made at '+str(timeAllowed))
            print('Sleeping until the next call can be made...')
            time.sleep(timeToWaitSeconds)
            print('Starting the next call now...')
            apirequest = requests.post(url, headers=adobeHeaders, data=body)
            readable = json.loads(apirequest.content.decode('utf-8'))
            if readable['result'] == 'success':
                print('Access successfully removed for ' + user)
            else:
                print('Access not removed for ' + user)

        else:
            readable = json.loads(apirequest.content.decode('utf-8'))
            if readable['result'] == 'success':
                print('Access successfully removed for ' + user)
            else:
                print('Acess not removed for ' + user)

#do it
getAdobeUsers()
