#!/bin/bash

# CS498 CCA - GCP Component Self-Check Script
# Use this to verify your deployment before running the autograder.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== CS498 CCA Setup Self-Check ===${NC}"

# 1. Check Environment Variables
echo -e "\n[1/6] Checking Environment Variables..."
MISSING_VARS=0
for var in PROJECT_ID REGION BUCKET_NAME DATASET_NAME; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}FAIL:${NC} \$$var is not set."
        MISSING_VARS=1
    else
        echo -e "${GREEN}OK:${NC} \$$var=${!var}"
    fi
done

if [ $MISSING_VARS -eq 1 ]; then
    echo -e "${RED}Error:${NC} Please set all required environment variables before running this script."
    exit 1
fi

# 2. Check GCS Bucket
echo -e "\n[2/6] Checking GCS Bucket..."
if gsutil ls -b "gs://${BUCKET_NAME}" >/dev/null 2>&1; then
    echo -e "${GREEN}OK:${NC} gs://${BUCKET_NAME} exists."
else
    echo -e "${RED}FAIL:${NC} Bucket gs://${BUCKET_NAME} not found."
fi

# 3. Check Cloud Functions
echo -e "\n[3/6] Checking Cloud Functions..."
FUNCTIONS=(
    "upload-kb"
    "process-kb-document"
    "retrieve-kb"
    "publish-ticket"
    "get-ticket-resolutions"
)

for func in "${FUNCTIONS[@]}"; do
    STATUS=$(gcloud functions describe "$func" --region "${REGION}" --gen2 --format="value(state)" 2>/dev/null)
    if [ "$STATUS" == "ACTIVE" ]; then
        URL=$(gcloud functions describe "$func" --region "${REGION}" --gen2 --format="value(serviceConfig.uri)")
        echo -e "${GREEN}OK:${NC} $func is ACTIVE. URL: $URL"
        
        # Check for public access (except for process-kb-document which is event-triggered)
        if [ "$func" != "process-kb-document" ]; then
            IAM_POLICY=$(gcloud run services get-iam-policy "$func" --region "${REGION}" --format="value(bindings)")
            if echo "$IAM_POLICY" | grep -q "allUsers"; then
                echo -e "    ${GREEN}OK:${NC} Publicly accessible (allow-unauthenticated)."
            else
                echo -e "    ${RED}FAIL:${NC} NOT publicly accessible. Use --allow-unauthenticated during deploy."
            fi
        fi

        # Specific check for process-kb trigger
        if [ "$func" == "process-kb-document" ]; then
            TRIGGER=$(gcloud functions describe "$func" --region "${REGION}" --gen2 --format="value(eventTrigger.eventType)" 2>/dev/null)
            if [[ "$TRIGGER" == *"storage.object.v1.finalized"* ]]; then
                echo -e "    ${GREEN}OK:${NC} Trigger set to GCS finalized event."
            else
                echo -e "    ${RED}FAIL:${NC} Trigger is NOT set to GCS finalized event (Found: $TRIGGER)."
            fi
        fi
    else
        echo -e "${RED}FAIL:${NC} $func is not ACTIVE or not found (Status: $STATUS)."
    fi
done

# 4. Check Pub/Sub
echo -e "\n[4/6] Checking Pub/Sub..."
if gcloud pubsub topics describe support-tickets >/dev/null 2>&1; then
    echo -e "${GREEN}OK:${NC} Topic 'support-tickets' exists."
else
    echo -e "${RED}FAIL:${NC} Topic 'support-tickets' not found."
fi

if gcloud pubsub subscriptions describe support-tickets-sub >/dev/null 2>&1; then
    echo -e "${GREEN}OK:${NC} Subscription 'support-tickets-sub' exists."
else
    echo -e "${RED}FAIL:${NC} Subscription 'support-tickets-sub' not found."
fi

# 5. Check BigQuery
echo -e "\n[5/6] Checking BigQuery Dataset and Tables..."
if bq show "${DATASET_NAME}" >/dev/null 2>&1; then
    echo -e "${GREEN}OK:${NC} Dataset '${DATASET_NAME}' exists."
    
    TABLES=("knowledge_chunks" "ticket_resolutions")
    for table in "${TABLES[@]}"; do
        if bq show "${DATASET_NAME}.${table}" >/dev/null 2>&1; then
            COUNT=$(bq query --use_legacy_sql=false --format=csv "SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET_NAME}.${table}\`" | tail -n 1)
            echo -e "${GREEN}OK:${NC} Table '${table}' exists ($COUNT rows)."
        else
            echo -e "${RED}FAIL:${NC} Table '${table}' not found."
        fi
    done
else
    echo -e "${RED}FAIL:${NC} Dataset '${DATASET_NAME}' not found."
fi

# 6. Check Dataflow
echo -e "\n[6/6] Checking Dataflow Job..."
RUNNING_JOBS=$(gcloud dataflow jobs list --region="${REGION}" --format="value(id)" --filter="state=Running")
if [ -n "$RUNNING_JOBS" ]; then
    echo -e "${GREEN}OK:${NC} Found running Dataflow job(s):"
    echo "$RUNNING_JOBS"
else
    echo -e "${RED}FAIL:${NC} No running Dataflow jobs found. Tickets will NOT be processed."
fi

echo -e "\n${GREEN}=== Check Complete ===${NC}"
