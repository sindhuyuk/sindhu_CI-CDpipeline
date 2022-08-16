	
import json
import boto3
import base64
import datetime
import os
from datetime import date
from botocore.exceptions import ClientError
AWS_REGION_NAME = '<your udpate region here>'
SNS_TOPIC_ARN = '<your update sns topic arn>'
ACCESS_KEY_SECRET_NAME = '<iam username>'
iam = boto3.client('iam')
secretmanager = boto3.client('secretsmanager')
sns = boto3.client('sns', region_name=eu-west2)
 
def create_key(iam_username):
    '''Generates a new access key on behalf of the user and stores the new
    access key in secrets manager. Then, send a notification email to users to
    notify them to rotate the key for their applications. It returns
    a JSON with status 200 if successful and 500 if error occurs.
 
    Arguments:
    iam_username - The iam user's username as a string.
    '''
 
    try:
        response = iam.create_access_key(UserName=iam_username)
        access_key = response['AccessKey']['AccessKeyId']
        secret_key = response['AccessKey']['SecretAccessKey']
        json_data = json.dumps(
            {'AccessKey': access_key, 'SecretKey': secret_key})
        secretmanager.put_secret_value(
            SecretId=iam_username, SecretString=json_data)
 
        iam_user_details = get_iam_user_details(iam_username)
 
        emailmsg = 'Hello,\n\n' \
            'A new access key has been created for key rotation. \n\n' \
            'Access Key Id: {access_key}\n' \
            'Secrets Manager Secret Id: {iam_username}'
 
        emailmsg = '{emailmsg}\n\n' \
            'Please obtain the new access key information from ' \
            'secrets manager using the secret Id provided above in ' \
            '{AWS_REGION_NAME} and update your application within 14 days ' \
            'to avoid interruption.\n'
 
        sns.publish(TopicArn=SNS_TOPIC_ARN, Message=emailmsg,
                    Subject='AWS Access Key Rotation: New key is available for '
                            '{iam_username}')
        print('New access key has been created for {iam_username}')
        return {'status': 200}
    except ClientError as e:
        print(e)
        return {"status": 500}
 
 
def deactive_key(iam_username):
    '''Finds the secret that stores the user's previous access key
    and mark it as inactive. Then, send a notification email to users to remind
    them to rotate the key for their applications. It returns
    a JSON with status 200 if successful and 500 if error occurs.
 
    Arguments:
    iam_username - The iam user's username as a string.
    '''
 
    try:
        previous_secret_value = secretmanager.get_secret_value(
            SecretId=iam_username, VersionStage='AWSPREVIOUS')
        previous_secret_data = json.loads(
            previous_secret_value['SecretString'])
        previous_access_key = previous_secret_data['AccessKey']
 
        iam_user_details = get_iam_user_details(iam_username)
 
        print(
            'deactivating access key {previous_access_key} '
            'for IAM user {iam_username}')
 
        iam.update_access_key(AccessKeyId=previous_access_key,
                              Status='Inactive', UserName=iam_username)
 
        emailmsg = 'Hello,\n\n' \
            'The previous access key {previous_access_key}'
 
        emailmsg = '{emailmsg} has been disabled for {iam_username}.\n\n' \
            'This key will be deleted in the next 14 days. ' \
            'If your application has lost access, be sure to update the ' \
            'access key.\n You can find the new key by looking up the secret ' \
            '"{iam_username}" under secrets manager via AWS Console ' \
            'in {AWS_REGION_NAME}.\n\n'
  
        sns.publish(
            TopicArn=SNS_TOPIC_ARN, Message=emailmsg,
            Subject='AWS Access Key Rotation: Previous key deactivated for '
                    '{iam_username}')
        print('Access Key has been deacivated')
        return {'status': 200}
    except ClientError as e:
        print(e)
        return {'status': 500}
 
 
def delete_key(iam_username):
    '''Deletes the deactivated access key in the given iam user. Returns
    a JSON with status 200 if successful, 500 for error and 400 for
    if secrets don't match
 
    Arguments:
    iam_username - The iam user's username as a string.
    '''
    try:
        previous_secret_value = secretmanager.get_secret_value(
            SecretId=iam_username, VersionStage='AWSPREVIOUS')
        previous_secret_string = json.loads(
            previous_secret_value['SecretString'])
        previous_access_key_id = previous_secret_string['AccessKey']
        print('previous_access_key_id: {previous_access_key_id}')
        keylist = iam.list_access_keys(UserName=iam_username)[
            'AccessKeyMetadata']
 
        for key in keylist:
            key_status = key['Status']
            key_id = key['AccessKeyId']
 
            print('key id: {key_id}')
            print('key status: {key_status}')
 
            if key_status == "Inactive":
                if previous_access_key_id == key_id:
                    print('Deleting previous access key from IAM user')
                    iam.delete_access_key(
                        UserName=iam_username, AccessKeyId=key_id)
                    print('Previous access key: '
                          '{key_id} has been deleted for user '
                          ' {iam_username}.')
                    return {'status': 200}
                else:
                    print(
                        'secret manager previous value doesn\'t match with '
                        'inactive IAM key value')
                    return {'status': 400}
            else:
                print('previous key is still active')
        return {'status': 200}
    except ClientError as e:
        print(e)
        return {'status': 500}
 
 
def lambda_handler(event, context):
    action = event["action"]
    iam_username = event["username"]
    status = {'status': 500}
 
    print('Detected Action: {action}')
    print('Detected IAM username: {iam_username}')
 
    if action == "create":
        status = create_key(iam_username)
    elif action == "deactivate":
        status = deactive_key(iam_username)
    elif action == "delete":
        status = delete_key(iam_username) 
    return status
