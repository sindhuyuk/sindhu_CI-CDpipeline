import boto3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dateutil import parser
import dateutil
from datetime import date
import json
import datetime
import botocore
import logging
from queue import Empty
from botocore.exceptions import ClientError
logger = logging.getLogger(__name__)
iam_client = boto3.client('iam')
secrets_client = boto3.client('secretsmanager')


def test_secretmanger_check(username):
    try:
        # print("2. checking sc secret exist or not ---------->")
        # username = 'testuseriamw'
        secret_details = secrets_client.describe_secret(SecretId=username)
        sc_status = secret_details['Name']
        print("Step2 User: "+ username + " Secret Found in " + sc_status)
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'ResourceNotFoundException':
            # logger.warn('Secret key not found return notfound ..')
            sc_status = "NotFound"
            print("Step2 User: "+ username + " SecretManager Secret " + sc_status)
        else:
            print("error nothing sc")
        return (sc_status)


def get_last_use(key_id):
    """
    Gets information about when and how a key was last used.

    :param key_id: The ID of the key to look up.
    :return: Information about the key's last use.
    """
    try:
        response = iam_client.get_access_key_last_used(AccessKeyId=key_id)
        last_used_date = response['AccessKeyLastUsed'].get(
            'LastUsedDate', None)
        username = response['UserName']
        print(username)
        print(last_used_date)
        # last_service = response['AccessKeyLastUsed'].get('ServiceName', None)
        # acive5dayscheck = date.today() - last_used_date
        print("check---value")
        if last_used_date == None:
            print("value is Null Never accessed ")
        elif last_used_date != None:
            # print("Key last accessed days ago checking ------>" + str(last_used_date) )
            tz = last_used_date.tzinfo
            diff = datetime.datetime.now(tz)-last_used_date
            diffdays = diff.days
            print(diffdays)
            if diffdays <= 5:
                print("Keys used since last 5 days" + username)
                print(diffdays)
                return (diffdays)

        # print("Key %s was last used by %s on %s to access %s.", key_id,response['UserName'], + last_used_date, last_service)
    except ClientError:
        logger.exception("Couldn't get last use of key %s.", key_id)
        raise
    else:
        return response
# print(response)


def create_key(username):
    try:
        paginatorlistkeys = iam_client.get_paginator('list_access_keys')
        sc=test_secretmanger_check(username)
        # print(sc)
        for response in paginatorlistkeys.paginate(UserName=username):
            # Get no of keys for users currently
            keystotal=(len(response['AccessKeyMetadata']))
            print(keystotal)
            username=user['UserName']
            IAM_UserName=username
            # response = iam_client.create_access_key(UserName=IAM_UserName)  
            # AccessKey = response['AccessKey']['AccessKeyId']
            # SecretKey = response['AccessKey']['SecretAccessKey']
            # json_data=json.dumps({'AccessKey':AccessKey,'SecretKey':SecretKey})
            # secrets_client.create_secret(Name=IAM_UserName,SecretString=json_data)
            # print("created secrete sucessfully ")
            if keystotal <= 2:
                if sc == 'NotFound':
                    print(sc)
                    response = iam_client.create_access_key(UserName=IAM_UserName)  
                    AccessKey = response['AccessKey']['AccessKeyId']
                    SecretKey = response['AccessKey']['SecretAccessKey']
                    json_data=json.dumps({'AccessKey':AccessKey,'SecretKey':SecretKey})
                    secmanagerv=secrets_client.create_secret(Name=IAM_UserName,SecretString=json_data)
                    print("Step_2  User:  Not Found Creating new one Secret and storing secret manager ----------")

                if sc == username:
                    print(sc)
                    response = iam_client.create_access_key(UserName=IAM_UserName)  
                    AccessKey = response['AccessKey']['AccessKeyId']
                    SecretKey = response['AccessKey']['SecretAccessKey']
                    json_data=json.dumps({'AccessKey':AccessKey,'SecretKey':SecretKey})
                    secmanagerv=secrets_client.put_secret_value(SecretId=IAM_UserName,SecretString=json_data)
                    print("Step_2  User:    Not Found Creating new one Secret and storing secret manager ----------")

         
            # if keystotal <= 2:
            #     print("running this code 2")      
            #     response = iam_client.create_access_key(UserName=IAM_UserName)
            #     AccessKey = response['AccessKey']['AccessKeyId']
            #     SecretKey = response['AccessKey']['SecretAccessKey']
            #     json_data=json.dumps({'AccessKey':AccessKey,'SecretKey':SecretKey})
            #     secmanagerv=secrets_client.create_secret(Name=IAM_UserName,SecretString=json_data)
            #     # Check secret is preset in secret manager or not  
            #     if sorted(sc) == sorted("NotFound"):
            #         print("notfount 2"+json_data)
            #         secmanagerv=secrets_client.create_secret(Name=IAM_UserName,SecretString=json_data)
            #         print("Step_2  User:  " + username + "  Not Found Creating new one Secret and storing secret manager ----------")
            #     if sorted(sc) == sorted(username):
            #         print("Step_2 User:  " + username + "  Found in existing secretmanager updating ----------")
            #         secmanagerv=secrets_client.put_secret_value(SecretId=IAM_UserName,SecretString=json_data)
            #         print(secmanagerv)   

        

    except ClientError as e:
        if e.response['Error']['Code'] == 'LimitExceeded':
            print("Step_2 User:  " + username + "  Already have 2 keys exists need to delete oldest one to progress")
    #     if sorted(sc) == sorted("NotFound"):
    #                 print("notfount 2"+json_data)
    #                 secmanagerv=secrets_client.put_secret_value(SecretId=IAM_UserName,SecretString=json_data) 
    #                 print("Step_2  User:  " + username + "  Not Found Creating new one Secret and storing secret manager ----------")
    #     if sorted(sc) == sorted(username):
    #                 print("fount"+json_data)
    #                 print("Step_2 User:  " + username + "  Found in existing secretmanager updating ----------")
    #                 secmanagerv=secrets_client.put_secret_value(SecretId=IAM_UserName,SecretString=json_data)
    #                 print(secmanagerv)  

# def lambda_handler(event, context):
try:
    marker = None
    paginator = iam_client.get_paginator('list_users')
    # Need to use a paginator because by default API call only returns 100 records
    for page in paginator.paginate(PaginationConfig={'PageSize': 100, 'StartingToken': marker}):
        MaxItems = 10
        u = page['Users']
        for user in u:
            keys = iam_client.list_access_keys(UserName=user['UserName'])
            for key in keys['AccessKeyMetadata']:
                active_for = date.today() - key['CreateDate'].date()
                # print("lenth of keys",len(key))
                # With active keys older than 90 days
                if key['Status'] == 'Active' and active_for.days <= 90:
                    print("Step_1. user: "+user['UserName'] + " --AccessKeyId-- " + key['AccessKeyId'] + " - " + str(
                        active_for.days) + " Old key rotation required creating new key .....")
                    # Creating new key
                    username = user['UserName']
                    create_key(username)

                    # check key when last used
                    key_id=key['AccessKeyId']
                    nodays=get_last_use(key_id)
                    if nodays <= 5:
                        print("Key ")
                        print(nodays)

                # Grace period 5 day on top 90 days over now 95 days and rquired to Inactivating the old key
                elif key['Status'] == 'Active' and active_for.days >= 5:
                    print(user['UserName'] + " - " + key['AccessKeyId'] + " - " + str(active_for.days) +
                          "Grace period 5 day on top 90 days over now Inactivating the old key")
                    # check its been used last 5 days or not
                    # key_id=key['AccessKeyId']
                    # get_last_use(key_id)
                    # print (get_last_use(key_id))
                    # acive5dayscheck = date.today() - get_last_use(response)
                    # if key['Status']=='Active' and acive5dayscheck.days <= 5:
                    #     print("Found keys which is lessthen 5 days old used ")
                    #     print(+ str(acive5dayscheck.days) + "value ")
                    # if

                    # iam_client.update_access_key(UserName=user['UserName'], AccessKeyId=key['AccessKeyId'], Status='Inactive')

except ClientError as e:
    print("An error has occurred attempting to rotate user %s access keys." %
          user['UserName'])

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
        iam_client.update_access_key(
            UserName=username, AccessKeyId=access_key, Status='Inactive')
        print("%s has been inactivated." % (access_key))
    except ClientError as e:
        print("The access key with id %s cannot be found" % access_key)
