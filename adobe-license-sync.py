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

cloud_id = 'lpa_bimbeats:dXMtd2VzdC0yLmF3cy5mb3VuZC5pbyQzM2RiMTFkZTI2NzA0MjVmYTA0ZWJhYTU4OTY4NWFkMyQzNDFkNWI3ODFkZjM0ZTg1OWZkZTA1OTQzYmM4NWM1ZA=='
api_key_id = 'AxQnmocBF3N7DMc-nPf1'
api_key = 'mJXhw019TT2SAbWvgpzwwQ'
es = Elasticsearch(
    cloud_id=cloud_id,
    api_key=(api_key_id, api_key),
)

#es = Elasticsearch(
#    cloud_id=cloud_id,
#    http_auth=('2366930620','eab3yac8dtc-WKA7kad')
#)


adobeOrgID = 'A2AE196C5C7874E00A495E82@AdobeOrg'
adobeClientID = '1298434b2be941218b2db69fac65222c'

def retrieveToken(validMinutes):
    now = datetime.now()
    now = now + timedelta(minutes=validMinutes)
    now = now.timestamp()
    now = math.ceil(now)

    adobePrivateKey = """-----BEGIN PRIVATE KEY-----
MIIEuAIBADANBgkqhkiG9w0BAQEFAASCBKIwggSeAgEAAoIBAQC7O68lPzzQE3NxBWTVGdjF8HfB
G5pKiDfB7RG9yBtY8LojU62BVvtm7+uBAYDRQ+VEBxfInRCSjR8oBrufr+TkLEahsB6Ui5TIm3L9
QhGFZZPL3wGTU9k7A5GBIIW9tYJhotu93llwIlRbJt465wdqymyOSAKsx/ApctpJfjwxYbLhPz55
cIs6pPhDSrmfUwtDtu/2Tiyc9SehL4FjXHGc7hPoeBnaLsH2nuPJqXVjc3ph4BVvkHKYSZJNbfXb
jGH6020yaf78hZn+GgZ/PkLcta/8u7cFToQ8Jvsq+F3K0ImGDoJJ77P1tGSysJfaZEruYjmAEFZD
XdYy3ZlZjLdZAgMBAAECgf9/cOCGOcTq3FJ3W3SGmFE0abkZd/BNSuqo1PR+ePYkU7Ze1VYD83Cr
YCKsbJmB1vT2mN1Xb5EYL3ZFiE+tIcxqgriQ1Y/7DAb5hNWADLhgVAOFgQVRgoEZ6hPgEIL33dQh
IPjxA6dc7AD/CjW5YgdqaN36+ojXkj+l9scdvw65jNmBX9/n7sXr3KpbSixwIc/oGOoCtVB1aKgB
mEKsWt1+9aoAzhRKAt1VkIwUylOQ2PchyiWi1Mj38fn5BWq/WWd3PYLFr9shSe8MxNYEIZau3Nrw
vRdXtDfJOq+xky7xCD+DMM50ncyyffn4D8b+jP/PGMLmXEH5x6Mjfj0P0dUCgYEAvmTV0GuAngts
Bw9GGopAYhSyWHVKKeJkq5e6ja4Kvzo0klj5GZgPuCvUptwUlo82xA/KmFmZM6zefKQJOqwnE5he
/nQ9MbuNBEYAv35i1BeIMzvnUoHQnkAELFAbjRXUWOv+E6ZXupBat9tkYRpg2ATy+zrwlHTnTko/
tysErI0CgYEA+8AH6FERFir72EYUvN2H011t5k/8jg2cb6yIBsfhngldFOXas7lbaj+xEb20l8lU
ikawzxmrs0bm8Q2qrZFwGiJVnV7Bu4aLCgTueOcx9Xh8ZedBzFY/vNz+fLITuM8c95tBjCy0nXr1
hH8XsnGqkxJuCcC4r1DLk2oT9qtS8P0Cf1BSOeGzeI80Ql64EtsfeAnosVSgJqmE2POLDyi2Q9Jo
u8UBxBUIEZmg5BWAwy7BPFl6T/31zqv+Qd5TVZFrDxE1Nt4iK67PcK5c2fPvXcIcK1lx7CTinyAj
4Z7QLM9YZj0dUhL4Ggqa26q046QTfMelTtyuANCggPSGXlrnyxECgYBrza+VLCHE/GMcGeaHedXQ
DRIird3YdrumlpspTC6xHhFeAY/Fpnoe5WdN0Y6j8PLiw6KzDKsZ+iKq1s9fxAfdKRbAbPNI+jRP
9gyoeVhLZWzftkfW2Jgyp+/SNe98FDSzUyiefgZZ6W15b3MWVtZUZG/6fSyY5mBGoAYsevDpgQKB
gF5sIBWJMytNkm/Jpz1gyI5vy2uYN1HuupZBgAPIRE1PpNAe9idLfKlktSMEh1eWLOcfHQ6azvP1
bmG1rr+Q8ftTbhC53jI0013HRaszGLyaLldsW7SP4ePzNZjbJAh5n+oW4UeWbzDyB7l5+8Zu1me7
osGNQFgTEQCXGHrZJux3
-----END PRIVATE KEY-----"""

    jwtPayload = {
        "exp":now,
        "iss":"A2AE196C5C7874E00A495E82@AdobeOrg",
        "sub":"E754382E644065130A495EA3@techacct.adobe.com",
        "https://ims-na1.adobelogin.com/s/ent_user_sdk": True,
        "aud":"https://ims-na1.adobelogin.com/c/1298434b2be941218b2db69fac65222c"
    }

    encodedJWT = jwt.encode(jwtPayload,adobePrivateKey,algorithm='RS256')
    adobeClientSecret = 'p8e-mBN25uTNVDZ_yhnK89Wt2LCFb5viTFuA'
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
