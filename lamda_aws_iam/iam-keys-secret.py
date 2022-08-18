# import boto3
# import logging
# from botocore.exceptions import ClientError

# logger = logging.getLogger(__name__)

# iam = boto3.resource('iam')

# client = boto3.client('iam') 
# response = client.list_users()
# for x in response['Users']:
#      print (x['UserName']) 

# def get_last_use(key_id):
#     """
#     Gets information about when and how a key was last used.

#     :param key_id: The ID of the key to look up.
#     :return: Information about the key's last use.
#     """
#     try:
#         response = iam.meta.client.get_access_key_last_used(AccessKeyId=key_id)
#         last_used_date = response['AccessKeyLastUsed'].get('LastUsedDate', None)
#         last_service = response['AccessKeyLastUsed'].get('ServiceName', None)
#         logger.info(
#             "Key %s was last used by %s on %s to access %s.", key_id,
#             response['UserName'], last_used_date, last_service)
#     except ClientError:
#         logger.exception("Couldn't get last use of key %s.", key_id)
#         raise
#     else:
#         return response
# # print(response)

import datetime
import json
from datetime import date
import dateutil
from dateutil import parser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import boto3
from botocore.exceptions import ClientError
iam_client = boto3.client('iam')
secrets_client = boto3.client('secretsmanager')


try:
    marker = None
    paginator = iam_client.get_paginator('list_users')
    # Need to use a paginator because by default API call only returns 100 records
    for page in paginator.paginate(PaginationConfig={'PageSize': 100, 'StartingToken': marker}):
        # print("Next Page : {} ".format(page['IsTruncated']))
        MaxItems=10
        u = page['Users']
        for user in u:
            keys = iam_client.list_access_keys(UserName=user['UserName'])
            for key in keys['AccessKeyMetadata']:
                active_for = date.today() - key['CreateDate'].date()
                # With active keys older than 90 days
                if key['Status']=='Active' and active_for.days <= 1:
                    print (user['UserName'] + " - " + key['AccessKeyId'] + " - " + str(active_for.days) + " days old Generating new key")
                    # creating new key 
                    # username=user['UserName']
                    # response = iam_client.create_access_key(UserName=username)                      
                    
                    
                    
                    
                    # username=user['UserName']
                    # IAM_UserName=username
                    # response = iam_client.create_access_key(UserName=IAM_UserName)  
                    # AccessKey = response['AccessKey']['AccessKeyId']
                    # SecretKey = response['AccessKey']['SecretAccessKey']
                    # json_data=json.dumps({'AccessKey':AccessKey,'SecretKey':SecretKey})
                    # secrets_client.create_secret(Name=IAM_UserName,SecretString=json_data)

                    
                # Grace period 5 day on top 90 days over now 95 days and rquired to Inactivating the old key          
                elif key['Status']=='Active' and active_for.days == 95:
                    print (user['UserName'] + " - " + key['AccessKeyId'] + " - " + str(active_for.days) + "Grace period 5 day on top 90 days over now Inactivating the old key")   
                    # if 
                    
                    iam_client.update_access_key(UserName=user['UserName'], AccessKeyId=key['AccessKeyId'], Status='Inactive') 

except ClientError as e:
    print("An error has occurred attempting to rotate user %s access keys." % user['UserName'])
    
# Delete an specified access key for a user
def delete_key(access_key, username):
    try:
        iam_client.delete_access_key(UserName=username, AccessKeyId=access_key)
        print("%s has been deleted." % (access_key))
    except ClientError as e:
        print("The access key with id %s cannot be found" % access_key)

# Create a new AWS access key and share it with the user via email
# def create_key(username):
#     access_key_metadata = iam_client.create_access_key(UserName=username)['AccessKey']
#     access_key = access_key_metadata['AccessKeyId']
#     print("New access key (%s) created for %s" % (access_key, username))

# Delete an specified access key for a user
def inactivatekey(access_key, username):
    try:
        iam_client.update_access_key(UserName=username, AccessKeyId=access_key, Status='Inactive')
        print("%s has been inactivated." % (access_key))
    except ClientError as e:
        print("The access key with id %s cannot be found" % access_key)
        


def create_key(username):
    try:
        IAM_UserName=username
        response = iam_client.create_access_key(UserName=IAM_UserName)  
        AccessKey = response['AccessKey']['AccessKeyId']
        SecretKey = response['AccessKey']['SecretAccessKey']
        json_data=json.dumps({'AccessKey':AccessKey,'SecretKey':SecretKey})
        secmanagerv=secrets_client.put_secret_value(SecretId=IAM_UserName,SecretString=json_data)
       
    except ClientError as e:
        print (e)
