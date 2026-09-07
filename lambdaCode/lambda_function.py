import json
import boto3
import uuid
from urllib.parse import parse_qs

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('dev-table-form-002')

def lambda_handler(event, context):
    body = parse_qs(event.get("body", ""))

    item = {
        "id": str(uuid.uuid4()),
        "name": body.get("name", [""])[0],
        "email": body.get("email", [""])[0],
        "message": body.get("message", [""])[0],
    }

    table.put_item(Item=item)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"success": True})
    }
