import datetime
import json
from datetime import date
import dateutil
from dateutil import parser
from curses import KEY_A1
import logging
import boto3
from botocore.exceptions import ClientError
import botocore
iam_client = boto3.client('iam')
secrets_client = boto3.client('secretsmanager')
logger = logging.getLogger(__name__)


iam = boto3.resource('iam')


def list_keys(user_name):
    """
    Lists the keys owned by the specified user.

    :param user_name: The name of the user.
    :return: The list of keys owned by the user.
    """
    try:
        keys = list(iam.User(user_name).access_keys.all())
        #
        if len(keys) > 0:  # this will privent error if any user have 0 keys
            logger.info("Got %s access keys for %s.", len(keys), user_name)
            # res = iam_client.list_access_keys(UserName=user_name)
            # accesskeydate = res['AccessKeyMetadata'][0]['CreateDate'].date()
            # currentdate = date.today()
            # active_days = currentdate - accesskeydate
            # print ("",active_days)
        else:
            print("User Dont have any keys to list ")

    except ClientError:
        logger.exception("Couldn't get access keys for %s.", user_name)
        raise
    else:

        return keys


def print_keys(current_user_name):
    """Gets and prints the current keys for a user."""
    print('-'*88)
    print("AWS Identity and Account Management access key Rotation Chekcing for user:", current_user_name)
    print('-'*88)
    current_keys = list_keys(current_user_name)
    print("The current user's keys are now:")
    # print (current_keys)
    print(*[f"{key.id}: {key.status} : " for key in current_keys], sep='\n')
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s: %(message)s')


def test_secretmanger_check(username):
    try:
        # print("2. checking sc secret exist or not ---------->")
        # username = 'testuseriamw'
        secret_details = secrets_client.describe_secret(SecretId=username)
        sc_status = secret_details['Name']
        print("Step2 User: " + username + " Secret Found in " + sc_status)
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'ResourceNotFoundException':
            # logger.warn('Secret key not found return notfound ..')
            sc_status = "NotFound"
            print("Step2 User: " + username +
                  " SecretManager Secret " + sc_status)
        else:
            print("error nothing sc")
        return (sc_status)


def create_key(username, keystotal):
    try:
        paginatorlistkeys = iam_client.get_paginator('list_access_keys')
        sc = test_secretmanger_check(username)
        print("Creating new Key pair .........................")
        for response in paginatorlistkeys.paginate(UserName=username):
            # Get no of keys for users currently
            # username=user['UserName']
            IAM_UserName = username
            response = iam_client.create_access_key(UserName=IAM_UserName)
            AccessKey = response['AccessKey']['AccessKeyId']
            SecretKey = response['AccessKey']['SecretAccessKey']
            json_data = json.dumps(
                {'AccessKey': AccessKey, 'SecretKey': SecretKey})
            if keystotal > 0 and keystotal < 2:  # Only one key present we can create new key and store it secret manager
                if sc == 'NotFound':
                    print(sc)
                    secrets_client.create_secret(
                        Name=IAM_UserName, SecretString=json_data)
                    print(
                        "Step_2  User:  Not Found Creating new one Secret and storing secret manager ----------")

                if sc == username:
                    print(sc)
                    secrets_client.put_secret_value(
                        SecretId=IAM_UserName, SecretString=json_data)
                    print(
                        "Step_2  User:    Not Found Creating new one Secret and storing secret manager ----------")

    except ClientError as e:
        if e.response['Error']['Code'] == 'LimitExceeded':
            print("Step_2 User:  " + username +
                  "  Already have 2 keys exists need to delete oldest one to progress")


def get_last_use(key_id):
    """
    Gets information about when and how a key was last used.

    :param key_id: The ID of the key to look up.
    :return: Information about the key's last use.
    """
    try:
        response = iam.meta.client.get_access_key_last_used(AccessKeyId=key_id)
        last_used_date = response['AccessKeyLastUsed'].get(
            'LastUsedDate', None)
        last_service = response['AccessKeyLastUsed'].get('ServiceName', None)
        logger.info(
            "Key %s was last used by %s on %s to access %s.", key_id,
            response['UserName'], last_used_date, last_service)
    except ClientError:
        logger.exception("Couldn't get last use of key %s.", key_id)
        raise
    else:
        return last_used_date


def update_key(user_name, key_id, activate):
    """
    Updates the status of a key.

    :param user_name: The user that owns the key.
    :param key_id: The ID of the key to update.
    :param activate: When True, the key is activated. Otherwise, the key is deactivated.
    """

    try:
        key = iam.User(user_name).AccessKey(key_id)
        if activate:
            key.activate()
        else:
            key.deactivate()
        logger.info(
            "%s key %s.", 'Activated' if activate else 'Deactivated', key_id)
    except ClientError:
        logger.exception(
            "Couldn't %s key %s.", 'Activate' if activate else 'Deactivate', key_id)
        raise


def delete_key(user_name, key_id):
    """
    Deletes a user's access key.

    :param user_name: The user that owns the key.
    :param key_id: The ID of the key to delete.
    """

    try:
        key = iam.AccessKey(user_name, key_id)
        key.delete()
        logger.info(
            "Deleted access key %s for %s.", key.id, key.user_name)
    except ClientError:
        logger.exception("Couldn't delete key %s for %s", key_id, user_name)
        raise


def lambda_handler(event, context):
    marker = None
    paginator = iam_client.get_paginator('list_users')
    # Need to use a paginator because by default API call only returns 100 records
    for page in paginator.paginate(PaginationConfig={'PageSize': 100, 'StartingToken': marker}):
        MaxItems = 10
        u = page['Users']
        for current_user_name in u:
            # Getting from list only user name to use it for below function
            current_user_name = current_user_name['UserName']
            print_keys(current_user_name)
            dayslimit = 90
            newkeydays = 5
            all_keys = list_keys(current_user_name)
            keys = iam_client.list_access_keys(UserName=current_user_name)[
                'AccessKeyMetadata']
            keystotal = len(all_keys)
            # If you have 2 keys listed then run below steps
            if len(all_keys) == 2:
                print("\n")
                key1_id = all_keys[0].id
                key2_id = all_keys[1].id
                # key1_id = all_keys[0].id
                # key2_id = all_keys[1].id
                for key in keys:
                    active_for_days_keys2 = date.today() - \
                        key['CreateDate'].date()
                    if key['Status'] == 'Active' and active_for_days_keys2.days >= dayslimit:
                        # print("\n")
                        print(key['UserName'], key['AccessKeyId'], key['Status'], key['CreateDate'],
                              "Key Rotation required as its older then:->", dayslimit)
                        # print("This Key Rotation as its above threshold days: ", dayslimit)

                    if key['Status'] == 'Active' and active_for_days_keys2.days == dayslimit:
                        print("\n")
                        print(key['UserName'], key['AccessKeyId'], key['Status'],
                              key['CreateDate'], "No Action required as its below:->", dayslimit)

                    # if new key rotated within last 5 days and old key not been used in 5 days then inactivate the old key
                    if key['Status'] == 'Active' and active_for_days_keys2.days == newkeydays:
                        # Getting old id using newkey  != condtion
                        existing_key = next(
                            key for key in keys if key != key['AccessKeyId'])
                        # Getting is there any activity since last 5 days for the old key if not we will disable old key
                        exitingkey_id = existing_key['AccessKeyId']
                        last_used_old_key = get_last_use(exitingkey_id)
                        print(last_used_old_key)
                        # if its not used within last5 days we are deactivating it
                        if last_used_old_key == None:
                            # print ("Old key is Not used since last 5 days ----",last_used_old_key)
                            print(
                                "Old key", existing_key['AccessKeyId'], existing_key['UserName'], "Deactivating key")
                            # :param user_name: The user that owns the key.
                            # :param key_id: The ID of the key to update.
                            # :param activate: When True, the key is activated. Otherwise, the key is deactivated.
                            update_key(
                                existing_key['UserName'], existing_key['AccessKeyId'], False)
                            print(
                                "New key", key['AccessKeyId'], "Please use this new Key and keys stored in secret manager already ")
                            
                    # Key which is inactive state will be deleted after 150 days or inactive below 190 days (first key will be 90+5= 95 days incativated and after 90 days it will be deleted and new key created)
                    if key['Status'] == 'Inactive' and active_for_days_keys2.days > 150 and active_for_days_keys2.days < 190:
                        print("\n")
                        print(key['UserName'], key['AccessKeyId'], key['Status'],key['CreateDate'], "Key Need to deleted as its as inactive morethen 150 days + rotation required :->", dayslimit)
                        delete_key(key['UserName'], key['AccessKeyId'])

            # If you have only 1 key listed then run below steps
            if len(all_keys) > 0 and len(all_keys) < 2:
                for key in keys:
                    active_for_days_keys1 = date.today() - \
                        key['CreateDate'].date()
                    if key['Status'] == 'Active' and active_for_days_keys1.days <= dayslimit:
                        print(key['UserName'], key['AccessKeyId'],
                              key['CreateDate'])
                        # Creating new keypair as only one exists so far
                        print(
                            "Need Key Rotation as its above threshold days: ", dayslimit)
                        print("\n")
                        create_key(current_user_name, keystotal)
                    if key['Status'] == 'Inactive' and active_for_days_keys1.days <= 90:
                        print("\n")
                        print(
                            "Only 1 keys availabel and Key Inactive state  and NO action requried as its below threshold days: ", dayslimit)

            else:
                len(all_keys) < 1



