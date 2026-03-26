import json
import time
import os
import requests
import subprocess


def get_function_url():
    """Retrieve the URL of the publish-ticket Cloud Function using gcloud"""
    try:
        region = os.environ.get("REGION", "us-central1")
        cmd = [
            "gcloud",
            "functions",
            "describe",
            "publish-ticket",
            "--region",
            region,
            "--gen2",
            "--format",
            "value(serviceConfig.uri)",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"✗ Error getting function URL: {e.stderr}")
        return None


CLOUD_FUNCTION_URL = get_function_url()
# or replace with the ticket publish function URL


def publish_tickets(input_file="test_data/tickets.jsonl"):
    """Read tickets and send POST requests to the Cloud Function"""
    url = CLOUD_FUNCTION_URL
    if not url:
        print("✗ Could not retrieve Cloud Function URL. Aborting.")
        return

    print(f"Publishing tickets to {url}...")

    headers = {"Content-Type": "application/json"}

    with open(input_file, "r") as f:
        for line in f:
            ticket = json.loads(line.strip())

            # Send POST request to Cloud Function
            try:
                response = requests.post(url, json=ticket, headers=headers)
                response.raise_for_status()
                result = response.json()
                print(
                    f"✓ Published ticket {ticket['ticket_id']} (Pub/Sub ID: {result.get('message_id')}): {ticket['subject']}"
                )
            except requests.exceptions.RequestException as e:
                print(f"✗ Error publishing ticket {ticket.get('ticket_id')}: {e}")

            # Small delay to simulate real-time
            time.sleep(1)


if __name__ == "__main__":
    publish_tickets()
