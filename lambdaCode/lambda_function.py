import json
import boto3
import uuid
import base64
from urllib.parse import parse_qs

# Initialize both DynamoDB and SES clients
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses', region_name='us-east-2') # Ensure region matches your SES setup

table = dynamodb.Table('dev-table-form-002')

# CRITICAL: Replace these with your verified SES emails
SENDER_EMAIL = "samosman001@gmail.com"
RECEIVER_EMAIL = "samosman001@gmail.com"

def lambda_handler(event, context):
    raw_body = event.get("body", "") or ""
    
    if event.get("isBase64Encoded", False):
        try:
            raw_body = base64.b64decode(raw_body).decode('utf-8')
        except Exception:
            pass

    name, email, message = "", "", ""
    parsed_successfully = False

    # Data parsing architecture
    if isinstance(raw_body, dict):
        name = raw_body.get("name", "")
        email = raw_body.get("email", "")
        message = raw_body.get("message", "")
    elif isinstance(raw_body, str) and raw_body.strip():
        try:
            body_data = json.loads(raw_body)
            if isinstance(body_data, dict):
                name = body_data.get("name", "")
                email = body_data.get("email", "")
                message = body_data.get("message", "")
                parsed_successfully = True
        except (json.JSONDecodeError, TypeError):
            pass

        if not parsed_successfully:
            parsed = parse_qs(raw_body)
            if parsed:
                name = parsed.get("name", [""])[0]
                email = parsed.get("email", [""])[0]
                message = parsed.get("message", [""])[0]

    # Clean data attributes
    name = str(name).strip()
    email = str(email).strip()
    message = str(message).strip()

    # 1. Save data structure to DynamoDB
    item = {
        "id": str(uuid.uuid4()),
        "name": name if name else "Anonymous",
        "email": email if email else "No Email Provided",
        "message": message if message else "No Message Provided"
    }
    table.put_item(Item=item)

    # 2. Trigger the Email via Amazon SES
    try:
        email_body = f"""
        New Form Submission Received!
        
        Details:
        ------------------------------
        ID: {item['id']}
        Name: {item['name']}
        Email: {item['email']}
        Message: {item['message']}
        ------------------------------
        """
        
        ses.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [RECEIVER_EMAIL]},
            Message={
                'Subject': {'Data': f"New Form Submission from {item['name']}"},
                'Body': {'Text': {'Data': email_body}}
            }
        )
        print("Email sent successfully via SES.")
    except Exception as e:
        print(f"Error sending email via SES: {str(e)}")
        # We don't fail the request completely if email fails but DB succeeded

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({"success": True, "id": item["id"]})
    }
