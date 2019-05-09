import boto3
from botocore.exceptions import ClientError
import json
import os
import time
import uuid
import decimal
import requests

client = boto3.client('ses')
sender = os.environ['SENDER_EMAIL']
subject = os.environ['EMAIL_SUBJECT']
configset = os.environ['CONFIG_SET']
convertkit_key = os.environ['CONVERTKIT_KEY']
charset = 'UTF-8'

dynamodb = boto3.resource('dynamodb')


def sendMail(event, context):
    print(event)

    try:
        data = event['body']
        content = 'From: ' + data['firstname'] + ' ' + data['lastname'] + \
            '<br/>Email: ' + data['email'] + '<br/>Message: ' + data['message']
        saveToDynamoDB(data)
        response = sendMailToUser(data, content)
        convertkit = addSubscriberPerson(data)
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message Id:"),
        print(response['MessageId'])
    return "Email sent!"


def list(event, context):
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    # fetch all records from database
    result = table.scan()

    #return response
    return {
        "statusCode": 200,
        "body": result['Items']
    }


def saveToDynamoDB(data):
    timestamp = int(time.time() * 1000)
    # Insert details into DynamoDB Table
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    item = {
        'id': str(uuid.uuid1()),
        'firstname': data['firstname'],
        'lastname': data['lastname'],
        'email': data['email'],
        'message': data['message'],
        'createdAt': timestamp,
        'updatedAt': timestamp
    }
    table.put_item(Item=item)
    return


def addSubscriberPerson(data):
    body = {
        "first_name": data['firstname'],
        "email": data['email'],
        "api_key": convertkit_key
    }
    return requests.post('https://api.convertkit.com/v3/forms/833798/subscribe',  json=body)


def sendMailToUser(data, content):
    # Send Email using SES
    return client.send_email(
        Source=sender,
        Destination={
            'ToAddresses': [sender],
        },
        Message={
            'Subject': {
                'Charset': charset,
                'Data': subject
            },
            'Body': {
                'Html': {
                    'Charset': charset,
                    'Data': content
                },
                'Text': {
                    'Charset': charset,
                    'Data': content
                }
            }
        }
    )
