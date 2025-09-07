import json
import os
import hmac
import hashlib
import base64
from datetime import datetime
import boto3

def lambda_handler(event, context):
    """
    Process Stripe webhook events and forward to EventBridge
    """
    try:
        # Get environment variables
        eventbridge_bus = os.environ['EVENTBRIDGE_BUS']
        stripe_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

        # Parse the incoming request
        if 'body' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No body in request'})
            }

        # Verify Stripe signature if secret is provided
        if stripe_secret:
            signature = event.get('headers', {}).get('Stripe-Signature', '')
            if not verify_stripe_signature(event['body'], signature, stripe_secret):
                return {
                    'statusCode': 401,
                    'body': json.dumps({'error': 'Invalid signature'})
                }

        # Parse the webhook payload
        try:
            if isinstance(event['body'], str):
                payload = json.loads(event['body'])
            else:
                payload = event['body']
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid JSON payload'})
            }

        # Extract event details
        event_type = payload.get('type', 'unknown')
        event_id = payload.get('id', 'unknown')

        # Prepare EventBridge event
        eventbridge_event = {
            'Time': datetime.utcnow(),
            'Source': 'stripe.webhook',
            'DetailType': f'Stripe {event_type}',
            'Detail': json.dumps(payload),
            'EventBusName': eventbridge_bus
        }

        # Send to EventBridge
        eventbridge = boto3.client('events')
        response = eventbridge.put_events(
            Entries=[eventbridge_event]
        )

        # Check for failed entries
        if response.get('FailedEntryCount', 0) > 0:
            print(f"Failed to send {response['FailedEntryCount']} events to EventBridge")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to forward event'})
            }

        print(f"Successfully processed Stripe event: {event_type} ({event_id})")

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'success'})
        }

    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def verify_stripe_signature(payload, signature, secret):
    """
    Verify Stripe webhook signature
    """
    try:
        if not signature or not secret:
            return False

        # Parse signature header
        signature_parts = {}
        for part in signature.split(','):
            if '=' in part:
                key, value = part.split('=', 1)
                signature_parts[key] = value

        if 't' not in signature_parts or 'v1' not in signature_parts:
            return False

        # Create signed payload
        signed_payload = f"{signature_parts['t']}.{payload}"

        # Create expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures
        provided_signature = signature_parts['v1']
        return hmac.compare_digest(expected_signature, provided_signature)

    except Exception as e:
        print(f"Signature verification error: {str(e)}")
        return False
