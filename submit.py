import json
import time

import requests

# === Fill in your submission info ===
YOUR_EMAIL = ""  # <Your Email>
SECRET = ""  # <Your Secret>

# === Fill in your deployed endpoint URLs ===
UPLOAD_KB_URL = ""  # https://<region>-<project>.cloudfunctions.net/upload-kb
RETRIEVE_KB_URL = ""  # https://<region>-<project>.cloudfunctions.net/retrieve-kb
PUBLISH_TICKET_URL = ""  # https://<region>-<project>.cloudfunctions.net/publish-ticket
GET_TICKET_RESOLUTIONS_URL = (
    ""  # https://<region>-<project>.cloudfunctions.net/get-ticket-resolutions
)

# === DO NOT MODIFY BELOW ===

# === Autograder endpoints (do not modify) ===
API_GATEWAY_URL = (
    "https://rta00ohom6.execute-api.us-east-1.amazonaws.com/prod/mp12-gcp-bigqueryml-rag"
)
CHECK_URL = "https://rta00ohom6.execute-api.us-east-1.amazonaws.com/prod/check"

POLL_INTERVAL_SECONDS = 15
POLL_TIMEOUT_SECONDS = 900  # 15 minutes max

# ── Validate config ──────────────────────────────────────────────────────────

required_values = {
    "YOUR_EMAIL": YOUR_EMAIL,
    "SECRET": SECRET,
    "UPLOAD_KB_URL": UPLOAD_KB_URL,
    "RETRIEVE_KB_URL": RETRIEVE_KB_URL,
    "PUBLISH_TICKET_URL": PUBLISH_TICKET_URL,
    "GET_TICKET_RESOLUTIONS_URL": GET_TICKET_RESOLUTIONS_URL,
}
missing_values = [name for name, value in required_values.items() if not value.strip() or value.startswith("[")]
if missing_values:
    raise SystemExit(f"Missing required values: {', '.join(missing_values)}")

# ── Step 1: Submit ───────────────────────────────────────────────────────────

input_payload = {
    "email": YOUR_EMAIL.strip(),
    "secret": SECRET.strip(),
    "upload_kb_url": UPLOAD_KB_URL.strip(),
    "retrieve_kb_url": RETRIEVE_KB_URL.strip(),
    "publish_ticket_url": PUBLISH_TICKET_URL.strip(),
    "get_ticket_resolutions_url": GET_TICKET_RESOLUTIONS_URL.strip(),
}

print("Submitting to autograder...")
try:
    response = requests.post(API_GATEWAY_URL, json=input_payload, timeout=30)
    response.raise_for_status()
except requests.RequestException as exc:
    raise SystemExit(f"Failed to submit: {exc}") from exc

try:
    response_data = response.json()
except ValueError:
    raise SystemExit(f"Unexpected response: {response.text}")

# Unwrap if API Gateway returned a double-encoded body
if isinstance(response_data, dict) and isinstance(response_data.get("body"), str):
    response_data = json.loads(response_data["body"])

submission_id = response_data.get("submission_id")
if not submission_id:
    raise SystemExit(f"No submission_id returned: {response_data}")

print(f"Submission accepted. ID: {submission_id}")
print(response_data.get("message", ""))

# ── Step 2: Poll /check ──────────────────────────────────────────────────────

print(f"\nPolling for results (every {POLL_INTERVAL_SECONDS}s, up to {POLL_TIMEOUT_SECONDS}s)...\n")

seen_logs = 0
elapsed = 0

while elapsed < POLL_TIMEOUT_SECONDS:
    time.sleep(POLL_INTERVAL_SECONDS)
    elapsed += POLL_INTERVAL_SECONDS

    try:
        check_resp = requests.get(
            CHECK_URL,
            params={"id": submission_id, "secret": SECRET.strip()},
            timeout=15,
        )
    except requests.RequestException as exc:
        print(f"[{elapsed}s] Poll error: {exc}")
        continue

    if check_resp.status_code == 403:
        raise SystemExit("Access denied: secret does not match.")

    if check_resp.status_code != 200:
        print(f"[{elapsed}s] Unexpected status {check_resp.status_code}, retrying...")
        continue

    try:
        data = check_resp.json()
    except ValueError:
        print(f"[{elapsed}s] Non-JSON response, retrying...")
        continue

    status = data.get("status", "PROCESSING")
    score = data.get("score", 0)
    logs = data.get("message", [])

    # Print any new log lines
    for line in logs[seen_logs:]:
        print(f"  {line}")
    seen_logs = len(logs)

    print(f"[{elapsed}s] status={status}  score={score}/100")

    if status in ("COMPLETED", "FAILED"):
        break
else:
    print(f"\nTimed out after {POLL_TIMEOUT_SECONDS}s. Check back later with ID: {submission_id}")
