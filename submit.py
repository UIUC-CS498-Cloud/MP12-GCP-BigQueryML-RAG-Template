import json

import requests

# === Fill in your submission info ===
YOUR_NETID = "[NETID]"  # <Your NetID>
YOUR_EMAIL = "[EMAIL_ADDRESS]"  # <Your Email>

# === Fill in your deployed endpoint URLs ===
UPLOAD_KB_URL = ""  # https://<region>-<project>.cloudfunctions.net/upload-kb
RETRIEVE_KB_URL = ""  # https://<region>-<project>.cloudfunctions.net/retrieve-kb
PUBLISH_TICKET_URL = ""  # https://<region>-<project>.cloudfunctions.net/publish-ticket
GET_TICKET_RESOLUTIONS_URL = (
    ""  # https://<region>-<project>.cloudfunctions.net/get-ticket-resolutions
)

# === Fill in the autograder API Gateway URL ===
API_GATEWAY_URL = (
    # "https://5lvtlkpp6hgzth3zajn5wihmgu0mfpex.lambda-url.us-east-1.on.aws/"
    ""  # TODO: fill in
)

REQUEST_TIMEOUT_SECONDS = 620

required_values = {
    "YOUR_NETID": YOUR_NETID,
    "YOUR_EMAIL": YOUR_EMAIL,
    "UPLOAD_KB_URL": UPLOAD_KB_URL,
    "RETRIEVE_KB_URL": RETRIEVE_KB_URL,
    "PUBLISH_TICKET_URL": PUBLISH_TICKET_URL,
    "GET_TICKET_RESOLUTIONS_URL": GET_TICKET_RESOLUTIONS_URL,
    "API_GATEWAY_URL": API_GATEWAY_URL,
}

missing_values = [name for name, value in required_values.items() if not value.strip()]
if missing_values:
    raise SystemExit(f"Missing required values: {', '.join(missing_values)}")

input_payload = {
    "netid": YOUR_NETID.strip(),
    "email": YOUR_EMAIL.strip(),
    "upload_kb_url": UPLOAD_KB_URL.strip(),
    "retrieve_kb_url": RETRIEVE_KB_URL.strip(),
    "publish_ticket_url": PUBLISH_TICKET_URL.strip(),
    "get_ticket_resolutions_url": GET_TICKET_RESOLUTIONS_URL.strip(),
}

try:
    response = requests.post(
        API_GATEWAY_URL.strip(),
        json=input_payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    print(f"Status: {response.status_code} {response.reason}")

    try:
        response_data = response.json()
    except ValueError:
        print("Response Text:\n", response.text)
        raise SystemExit(0)

    if isinstance(response_data, dict) and "body" in response_data:
        response_body = response_data["body"]
        if isinstance(response_body, str):
            try:
                response_data = json.loads(response_body)
            except json.JSONDecodeError:
                response_data = response_body
        else:
            response_data = response_body

    if isinstance(response_data, dict) and "message" in response_data:
        print("Message:\n", response_data["message"])
    else:
        print("Response JSON:\n", json.dumps(response_data, indent=2))
except requests.RequestException as exc:
    raise SystemExit(f"Failed to invoke autograder API: {exc}") from exc
