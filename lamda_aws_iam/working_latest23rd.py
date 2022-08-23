from math import fabs
from tkinter.tix import Tree
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
        return (sc_status)
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'ResourceNotFoundException':
            # logger.warn('Secret key not found return notfound ..')
            sc_status = "None"
            print("Step2 User: "+ username + " SecretManager Secret " + sc_status)
            return (sc_status)
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
def delete_inactive_access_key(username):
    try:
        user = username
        
        for access_key in iam_client.list_access_keys(UserName = user)['AccessKeyMetadata']:
            active_for = date.today() - access_key['CreateDate'].date()
            
            if access_key['Status'] == 'Inactive' and active_for.days <= 5:
                # username = user['UserName']
                print ("\n======================Checking for INACTIVE keys if any will rotation older then 75 days===========")                
                sc=iam_client.delete_access_key(UserName = user,AccessKeyId = access_key['AccessKeyId'])
                print("\nStep_1. Found user "+ user +"  : Key2  Inactive since   "+ str(active_for.days) +"   Days Old key  ----------------- [Deleted]")
                # print('Deleting access key {0}.'.format(key['AccessKeyId']) +username) 
    except ClientError as e:
        print("An error has occurred attempting to rotate user %s access keys." %
            username)
        error = "Error"
        return (error)
    



def inactivatekey(access_key, username):
    try:
        iam_client.update_access_key(
            UserName=username, AccessKeyId=access_key, Status='Inactive')
        print("%s has been inactivated." % (access_key))
    except ClientError as e:
        print("The access key with id %s cannot be found" % access_key)


# def lambda_handler(event, context):
try:
    
    marker = None
    paginator = iam_client.get_paginator('list_users')
    # Need to use a paginator because by default API call only returns 100 records
    for page in paginator.paginate(PaginationConfig={'PageSize': 100, 'StartingToken': marker}):
        MaxItems = 10
        u = page['Users']
        print("================================IAM checking keys Rotation ==========================================")
        for user in u:
            keys = iam_client.list_access_keys(UserName=user['UserName'])
            for key in keys['AccessKeyMetadata']:
                active_for = date.today() - key['CreateDate'].date()
                # active_for=str[active_for.days]  
                print(active_for)              
                # With active keys older than 90 days
                if key['Status'] == 'Active' and active_for.days <= 90:
                    print("Step_1. Found user: "+user['UserName'] + " --AccessKeyId-- " + key['AccessKeyId'] + " - " + str(
                        active_for.days) + " Older key Need rotation ==================== [Checking for Inactvie keys]\n\n")
                    # check inactive key for this current user and if any present  delete
                    username = user['UserName']
                    # deleteinactive=delete_inactive_access_key(username)
                    user = username        
                    for access_key in iam_client.list_access_keys(UserName = user)['AccessKeyMetadata']:
                        active_for = date.today() - access_key['CreateDate'].date()
                            
                        if access_key['Status'] == 'Inactive' and active_for.days <= 5:
                            # username = user['UserName']
                            print ("\n======================Checking for INACTIVE keys if any will rotation older then 75 days===========")                
                            sc=iam_client.delete_access_key(UserName = user,AccessKeyId = access_key['AccessKeyId'])
                            print ("Step_1. Found user "+ user +"  : Key2  Inactive since     Days Old key  ----------------- [Deleted]"+ str(active_for.days))
                            # print('Deleting access key {0}.'.format(key['AccessKeyId']) +username) 
                            print("resource deleted ....")
                            IAM_UserName=username
                            # check secret creation or update required ?                           
                            # Creating new key 
                            if test_secretmanger_check(username) == 'None':
                                IAM_UserName=username
                                response = iam_client.create_access_key(UserName=IAM_UserName)  
                                AccessKey = response['AccessKey']['AccessKeyId']
                                SecretKey = response['AccessKey']['SecretAccessKey']
                                json_data=json.dumps({'AccessKey':AccessKey,'SecretKey':SecretKey})
                                secmanagerv=secrets_client.create_secret(Name=IAM_UserName,SecretString=json_data)
                                print("Step_2  User:  Not Found Creating new one Secret and storing secret manager ----------")
                            if test_secretmanger_check(username) == username:
                                response = iam_client.create_access_key(UserName=IAM_UserName)  
                                AccessKey = response['AccessKey']['AccessKeyId']
                                SecretKey = response['AccessKey']['SecretAccessKey']
                                json_data=json.dumps({'AccessKey':AccessKey,'SecretKey':SecretKey})
                                secmanagerv=secrets_client.put_secret_value(SecretId=IAM_UserName,SecretString=json_data)
                                print("Step_2  User:  Found Creating new one Secret and storing secret manager ----------")
                            
                    # except ClientError as e:
                    #     print("An error has occurred attempting to rotate user %s access keys." %
                    #         username)               

                # Grace period 5 day on top 90 days over now 95 days and rquired to Inactivating the old key
                elif key['Status'] == 'Active' and active_for.days >= 5:
                    print(user['UserName'] + " - " + key['AccessKeyId'] + " - " + str(active_for.days) +
                          "XXXXXXXXXX  Grace period 5 day on top 90 days over now Inactivating the old key\n\n")
                    # iam_client.update_access_key(UserName=user['UserName'], AccessKeyId=key['AccessKeyId'], Status='Inactive')
except ClientError as e:
    print("An error has occurred attempting to rotate user %s access keys." %
          user['UserName'])
