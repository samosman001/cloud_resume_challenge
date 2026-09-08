import json
import boto3
import uuid
import base64
from urllib.parse import parse_qs

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('dev-table-form-002')

def lambda_handler(event, context):
    # CRITICAL: Print the event to CloudWatch for your own tracking
    print("RAW EVENT RECEIVED FROM API GATEWAY:", json.dumps(event))

    raw_body = event.get("body", "") or ""
    
    # 1. Handle Base64 encoding
    if event.get("isBase64Encoded", False):
        try:
            raw_body = base64.b64decode(raw_body).decode('utf-8')
        except Exception as e:
            print(f"Base64 decode failed: {e}")

    name, email, message = "", "", ""
    parsed_successfully = False

    # 2. Case A: Body is already a pre-parsed dictionary
    if isinstance(raw_body, dict):
        name = raw_body.get("name", "")
        email = raw_body.get("email", "")
        message = raw_body.get("message", "")
        parsed_successfully = True
        
    # 3. Case B: Body is a string (JSON or URL-Encoded)
    elif isinstance(raw_body, str) and raw_body.strip():
        # Try JSON first
        try:
            body_data = json.loads(raw_body)
            if isinstance(body_data, dict):
                name = body_data.get("name", "")
                email = body_data.get("email", "")
                message = body_data.get("message", "")
                parsed_successfully = True
        except (json.JSONDecodeError, TypeError):
            pass

        # Try URL-Encoded Form Data if JSON didn't catch anything
        if not parsed_successfully:
            parsed = parse_qs(raw_body)
            if parsed:
                # parse_qs returns lists (e.g. {"name": ["John"]}), extract the 0th element safely
                name = parsed.get("name", [""])[0]
                email = parsed.get("email", [""])[0]
                message = parsed.get("message", [""])[0]
                parsed_successfully = True

    # 4. Fallback debug step: If everything is still empty, let's look for multipart form-data
    # or nested keys, and save the raw body so you can inspect it in DynamoDB.
    if not name and not email and not message:
        name = "DEBUG_EMPTY_FORM"
        message = f"Raw body received was: {str(raw_body)[:500]}"

    item = {
        "id": str(uuid.uuid4()),
        "name": str(name).strip(),
        "email": str(email).strip(),
        "message": str(message).strip()
    }

    table.put_item(Item=item)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps({"success": True, "id": item["id"]})
    }
