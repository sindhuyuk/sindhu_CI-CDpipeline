import boto3
from datetime import datetime, timezone
import json

client = boto3.client('iam')
paginator = client.get_paginator('list_users')
current_date=datetime.now(timezone.utc)
max_key_age = 90               
def lambda_handler(event, context):
transactionId = event['queryStringParameters']['keyRotation']
#print(transactionId)

if transactionId == 'TRUE':
     print('key rotation parameter is = to TRUE')
     return key_rotation()
else:
     print('key rotation parameter is something else and NOT = TRUE')

#return key_rotation()
return 'the function has excuted'
    
def key_rotation():

expiredUsers = {}

lst = []
for response in paginator.paginate():
     for user in response['Users']:
            username = user['UserName']
            #print(user)
            
            list_key = client.list_access_keys(UserName=username,MaxItems=100)
            #print(list_key)
            
            for accesskey in list_key['AccessKeyMetadata']:
                accesskey_id = accesskey['AccessKeyId']
                #print(accesskey_id)
                key_creation_date = accesskey['CreateDate']
                #print(key_creation_date)
                
                age = (current_date - key_creation_date).days
                #print("This key is so many days old:",age)
                
                if age > max_key_age:
                    #print("EXPIRED:",age,username)
                    #Build up the body of the json reponse
                    #expiredUsers['expiredUsers'] = username
                    #expiredUsers['age'] = age
                    #print(expiredUsers)
                    lst.append(username)
                else:
                    print("NOT EXPIRED:",age,username)
print(lst)
responseObject = {}
responseObject['statusCode'] = 200
responseObject['headers'] = {}
responseObject['headers']['Content-Type'] = 'application/json'
responseObject['body'] = json.dumps(lst)
return responseObject
