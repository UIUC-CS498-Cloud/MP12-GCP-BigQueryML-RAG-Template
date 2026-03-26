import functions_framework
from google.cloud import pubsub_v1
import os
import json
import uuid
from datetime import datetime, timezone

# Initialize Pub/Sub publisher client
publisher = pubsub_v1.PublisherClient()

PROJECT_ID = os.environ.get("PROJECT_ID")
TOPIC_NAME = os.environ.get("TOPIC_NAME", "support-tickets")


@functions_framework.http
def publish_ticket(request):
    """
    HTTP Cloud Function to publish a support ticket to Pub/Sub.

    Input (JSON):
        {
            "ticket_id":     "optional-string (auto-generated if omitted)",
            "customer_tier": "premium | standard",
            "subject":       "string",
            "message":       "string",
            "timestamp":     "optional ISO-8601 string (defaults to now)"
        }

    Output (JSON):
        {
            "message_id": "<pubsub-message-id>",
            "ticket_id": "<ticket-id>"
        }
    """
    # ── CORS pre-flight ──────────────────────────────────────────────────────
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    if request.method == "OPTIONS":
        return ("", 204, {**cors_headers, "Access-Control-Max-Age": "3600"})

    # ── Parse request ────────────────────────────────────────────────────────
    request_json = request.get_json(silent=True)
    if not request_json:
        return (
            json.dumps({"error": "Request body must be JSON"}),
            400,
            cors_headers,
        )

    required_fields = ["customer_tier", "subject", "message"]
    missing = [f for f in required_fields if f not in request_json]
    if missing:
        return (
            json.dumps({"error": f"Missing required fields: {missing}"}),
            400,
            cors_headers,
        )

    # ── Build ticket payload ─────────────────────────────────────────────────
    ticket = {
        "ticket_id": request_json.get("ticket_id", uuid.uuid4().hex[:8]),
        "customer_tier": request_json["customer_tier"],
        "subject": request_json["subject"],
        "message": request_json["message"],
        "timestamp": request_json.get(
            "timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ),
    }

    # ── Publish to Pub/Sub ───────────────────────────────────────────────────
    # TODO: Publish the ticket JSON to the Pub/Sub topic
    # 1. Get the topic_path using publisher.topic_path(PROJECT_ID, TOPIC_NAME)
    # 2. Encode the ticket dictionary as a JSON string and then to bytes (UTF-8)
    # 3. Publish to the topic using publisher.publish()
    # 4. Wait for the message_id by calling future.result()

    message_id = "placeholder-id"
    return (
        json.dumps({"message_id": message_id, "ticket_id": ticket["ticket_id"]}),
        200,
        cors_headers,
    )
