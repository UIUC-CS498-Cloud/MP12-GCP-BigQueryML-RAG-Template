# BigQuery ML + RAG Support Ticket System - Student Guide

Welcome to the BigQuery ML + RAG Support Ticket System project! In this project, you will build a real-time customer support ticket processing system using Google Cloud Platform (GCP).

## Project Overview

You will implement a system that demonstrates:

1. **BigQuery as Vector Database** - Store and search document embeddings.
2. **RAG (Retrieval-Augmented Generation)** - Ground an LLM (Gemini) in company policies.
3. **Streaming Analytics** - Build a pipeline: Pub/Sub → Dataflow → BigQuery.
4. **Vector Search** - Use BigQuery's `ML.DISTANCE` for semantic retrieval.

### Architecture

```
Knowledge Base Pipeline (Batch):
Markdown knowledge documents → Cloud Storage → chunking + embedding → BigQuery vector table

Ticket Processing Pipeline (Streaming):
Tickets → Pub/Sub → Dataflow → [RAG: Vector Search + Gemini] → BigQuery result table
```

---

## Part 0: Prerequisites & Setup

### 0.0 Claim GCP Credits if available

Spring 2026:

> Claim [HERE](https://urldefense.com/v3/__https://gcp.secure.force.com/GCPEDU?cid=i7scApKRA7*2F1tpCSTefKMF8Rpz290MrS7EojCfb7uBlj3vshN3UtjRkQvV9VhDOe*__;JS8!!DZ3fjg!95YZsYxbDy28eoTXKA2ZNngQUjsRILlzA1ByS9zmdeAdq_dpX6OA69vQpViO0P7vynjEkIoM3SL2Uv_VJHYGCBMUhIClcDo$)
>
> Important: you need your `@illinois.edu` / UIUC email to redeem the education credit, but you should apply that credit to a personal Google Cloud account because UIUC-managed accounts do not support using GCP directly.
>
> You can request a coupon from the URL and redeem it until: 5/13/2026
>
> Coupon valid through: 1/13/2027

### 0.1 Environment setup

First clone the repository:

```bash
git clone https://github.com/UIUC-CS498-Cloud/MP12-GCP-BigQueryML-RAG-Template.git
cd MP12-GCP-BigQueryML-RAG-Template
```

Then ensure you have the [Google Cloud CLI installed](https://cloud.google.com/sdk/docs/install), and authenticate your CLI with your Google account:

```bash
gcloud auth login
```

### 0.2 Create or Select a GCP Project

Create a GCP project in your personal Google Cloud account and attach your redeemed billing credit to it.

```bash
# Create a new project (project ID must be globally unique)
gcloud projects create YOUR_PROJECT_ID --name="YOUR_PROJECT_NAME"

# Set it as the active project
gcloud config set project YOUR_PROJECT_ID
```

`PROJECT_ID` is the globally unique identifier used by GCP and CLI commands, while `PROJECT_NAME` is the human-readable display name you see in the console.

### 0.3 Enable APIs

Enable the necessary services for this project:

```bash
gcloud services enable \
  bigquery.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  dataflow.googleapis.com \
  cloudfunctions.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  eventarc.googleapis.com
```

### 0.4 Setup Environment

1. Create a `.env` file based on `.env.example`:

   ```bash
   PROJECT_ID=your-project-id
   REGION=us-central1
   BUCKET_NAME=your-unique-bucket-name
   DATASET_NAME=support_analytics
   ```

   Note: `BUCKET_NAME` needs to be globally unique in GCP, so add your name or something.

2. Initialize the environment (do this every time you open a new terminal):

   ```bash
   source gcloud_init.sh
   ```

3. Create the BigQuery Dataset:
   ```bash
   bq mk --location=US ${DATASET_NAME}
   ```

---

## Part 1: Knowledge Base Pipeline (Batch Processing)

In this section, you will implement a pipeline to upload, process, and retrieve knowledge documents.

You need to complete the following Cloud Functions (look for `TODO` comments):

- **`functions/upload_kb/main.py`**: Upload a knowledge document to GCS.
- **`functions/process_kb/main.py`**: Process a knowledge document to generate embeddings and store them in BigQuery.
- **`functions/retrieve_kb/main.py`**: Retrieve knowledge documents from BigQuery.

### 1.1 Setup Cloud Storage

```bash
# Create bucket
gsutil mb -l ${REGION} gs://${BUCKET_NAME}
```

### 1.2 Prepare BigQuery Table

BigQuery can be used as a **serverless** vector database (a cool GCP-only feature as of Spring 2026!).
This table will store the knowledge document chunks and their embeddings.

```bash
bq query --use_legacy_sql=false "
CREATE TABLE \`${PROJECT_ID}.${DATASET_NAME}.knowledge_chunks\` (
  chunk_id STRING NOT NULL,
  source_document STRING NOT NULL,
  text STRING NOT NULL,
  embedding ARRAY<FLOAT64>,
  category STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);"
```

### 1.3 Deploy & Test `upload-kb`

**Deploy:**

```bash
cd functions/upload_kb
# Deploy or update cloud function with name `upload-kb`
gcloud functions deploy upload-kb \
  --gen2 \
  --runtime python312 \
  --region ${REGION} \
  --source . \
  --entry-point upload_kb \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars BUCKET_NAME=${BUCKET_NAME}
# Tip: you can pass environment variables using --set-env-vars, and cloud function can access it using os.environ.get("ENV_VAR_NAME")
```

**Test:**

```bash
# Get the function URL
URL=$(gcloud functions describe upload-kb --region ${REGION} --gen2 --format="value(serviceConfig.uri)")

# Upload a sample file
echo "This is a test document." > test_doc.txt
curl -X POST $URL -F "file=@test_doc.txt"

# Verify in bucket
gsutil ls gs://${BUCKET_NAME}/knowledge-base/
```

### 1.4 Deploy & Test `process-kb-document`

This function is triggered when a file is uploaded to the 'knowledge-base/' folder in Cloud Storage.
It should implement an **upsert strategy**: before inserting new chunks, delete any existing rows in BigQuery with the same `source_document` so re-uploading a document does not create duplicates.

**Deploy:**

```bash
cd functions/process_kb
gcloud functions deploy process-kb-document \
  --gen2 \
  --runtime python312 \
  --region ${REGION} \
  --source . \
  --entry-point process_kb_document \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=${BUCKET_NAME}" \
  --memory 1Gi \
  --timeout 540s \
  --set-env-vars DATASET_NAME=${DATASET_NAME}
```

If the deploy fails with `Permission denied while using the Eventarc Service Agent`, this usually means you just enabled `eventarc.googleapis.com` and need to wait a few minutes for the Eventarc service agent and IAM permissions to propagate. Wait a few minutes, then rerun the exact same deploy command.

If the deploy instead fails with `The Cloud Storage service account for your bucket is unable to publish to Cloud Pub/Sub topics in the specified project`, waiting will not fix it. Grant the bucket's Cloud Storage service agent the Pub/Sub Publisher role:

```bash
GCS_SA=$(gcloud storage service-agent --project=${PROJECT_ID})

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${GCS_SA}" \
  --role="roles/pubsub.publisher"
```

Then rerun the same `gcloud functions deploy process-kb-document ...` command.

**Trigger Processing:**
Upload your knowledge base documents in `kb_docs/` folder:

```bash
URL=$(gcloud functions describe upload-kb --region ${REGION} --gen2 --format="value(serviceConfig.uri)")
for file in kb_docs/*.md; do
  curl -X POST $URL -F "file=@$file"
done
```

**Monitor Logs:**

```bash
gcloud functions logs read process-kb-document --gen2 --region ${REGION} --limit 50
```

or go to Cloud Console -> Cloud Functions -> process-kb-document -> Logs to check the logs.

### 1.5 Deploy & Test `retrieve-kb`

This function is used to get a RAG retrieval result from the knowledge base.

**Deploy:**

```bash
cd functions/retrieve_kb
gcloud functions deploy retrieve-kb \
  --gen2 \
  --runtime python312 \
  --region ${REGION} \
  --source . \
  --entry-point retrieve_kb \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars DATASET_NAME=${DATASET_NAME}
```

**Test:**

```bash
URL=$(gcloud functions describe retrieve-kb --region ${REGION} --gen2 --format="value(serviceConfig.uri)")
curl -X POST $URL -H "Content-Type: application/json" -d '{"text": "I have a question about refund policy", "n": 2}'
```

You should see a JSON response with the retrieved knowledge base chunks.

---

## Part 2: Streaming Ticket Pipeline

In this section, you will implement a streaming pipeline to process customer support tickets. In reality, support tickets can arrive in a bursty manner, so a streaming pipeline is more scalable and widely used for this type of workload.

In this MP, we define a ticket as a JSON object with the following fields:

- `customer_tier`: The tier of the customer (premium, standard, or enterprise)
- `subject`: The subject of the ticket (e.g. "Urgent: Refund still pending")
- `message`: The message of the ticket (e.g. "Hi team, I have a question about refund policy, ...")

You will implement the following Cloud Functions:

- **`functions/publish_ticket/main.py`**: Publish a ticket to Pub/Sub
- **`functions/get_ticket_resolutions/main.py`**: Get ticket resolutions from BigQuery

And a Dataflow job to process tickets.

### 2.1 Create Pub/Sub Topic & Subscription

```bash
# creates a topic named support-tickets
gcloud pubsub topics create support-tickets
gcloud pubsub subscriptions create support-tickets-sub --topic support-tickets --ack-deadline 60
```

### 2.2 Deploy & Test `publish-ticket`

**Deploy:**

```bash
cd functions/publish_ticket
gcloud functions deploy publish-ticket \
  --gen2 \
  --runtime python312 \
  --region ${REGION} \
  --source . \
  --entry-point publish_ticket \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=${PROJECT_ID},TOPIC_NAME=support-tickets
# change --set-env-vars if you use a different topic name
```

**Test:**

```bash
URL=$(gcloud functions describe publish-ticket --region ${REGION} --gen2 --format="value(serviceConfig.uri)")
curl -X POST $URL -H "Content-Type: application/json" -d '{
    "customer_tier": "premium",
    "subject": "Urgent: Refund still pending",
    "message": "I requested a refund 3 days ago."
  }'
```

### 2.3 Create Output BigQuery Table

This table will store the ticket resolutions. Not all fields are tested during autograder, but you should try to implement all of them.

```bash
bq query --use_legacy_sql=false "
CREATE TABLE \`${PROJECT_ID}.${DATASET_NAME}.ticket_resolutions\` (
  ticket_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  customer_tier STRING,
  subject STRING,
  message STRING,
  retrieved_kb_chunks ARRAY<STRUCT<text STRING, source_document STRING, similarity_score FLOAT64>>,
  top_kb_source STRING,
  category STRING,
  priority STRING,
  suggested_solution STRING,
  kb_facts_used ARRAY<STRING>,
  retrieval_confidence FLOAT64,
  processing_time_ms INT64,
  solution_contains_kb_keywords BOOL,
  processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);"
```

### 2.4 Dataflow Pipeline Implementation

The dataflow is the actual _compute_ resource that processes each ticket. It consumes the tickets in pub/sub, do a RAG, and write the LLM response to BigQuery result table, and is scalable.

> Note: dataflow is **NOT** serverless; running with one e2-small instance costs ~$3.5 per day.
>
> You should stop the dataflow job when you are not working on this MP.

**Set up Virtual Environment:**

```bash
cd dataflow
# Install uv if not already present: pip install uv
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

Complete the implementation in `dataflow/ticket_processor.py`.

**Deploy Dataflow Job:**

```bash
source .venv/bin/activate
uv pip install "build" "setuptools>=68" "wheel"
python3 ticket_processor.py \
  --project=${PROJECT_ID} \
  --region=${REGION} \
  --runner=DataflowRunner \
  --streaming \
  --num_workers=1 \
  --machine_type=e2-small \
  --setup_file=$(pwd)/setup.py
```

If submission fails with a `stage_file_with_retry ... 403` error, see [Dataflow submission fails with 403](debug.md#dataflow-submission-fails-with-stage_file_with_retry--403) in the debugging guide.

If workers fail to start with a `ZONE_RESOURCE_POOL_EXHAUSTED` error, see [Dataflow Worker Pool Exhausted](debug.md#dataflow-worker-pool-exhausted) in the debugging guide.

> Note: this python script is only a **launcher**; the actual dataflow job will run in GCP. You can kill this python process after the job is launched.

**Test Dataflow Job:**

Publish a ticket to Pub/Sub

```bash
URL=$(gcloud functions describe publish-ticket --region ${REGION} --gen2 --format="value(serviceConfig.uri)")
curl -X POST $URL -H "Content-Type: application/json" -d '{
    "customer_tier": "premium",
    "subject": "Urgent: Refund still pending",
    "message": "I requested a refund 3 days ago."
  }'
```

Check the ticket resolution in BigQuery:

```bash
bq query --use_legacy_sql=false "SELECT ticket_id, category, suggested_solution FROM \`${PROJECT_ID}.${DATASET_NAME}.ticket_resolutions\` LIMIT 10;"
```

### 2.5 Deploy `get-ticket-resolutions`

To make it easier to autograder, we will use a function to query the ticket resolutions.

**Deploy:**

```bash
cd functions/get_ticket_resolutions
gcloud functions deploy get-ticket-resolutions \
  --gen2 \
  --runtime python312 \
  --region ${REGION} \
  --source . \
  --entry-point get_ticket_resolutions \
  --trigger-http \
  --allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars PROJECT_ID=${PROJECT_ID},DATASET_NAME=${DATASET_NAME}
```

---

## Part 3: Testing & Debugging

- **Batch Test:** Run `python3 test_data/publish_tickets.py` to send multiple tickets at once.
- **Verify in BigQuery:**
  ```bash
  bq query --use_legacy_sql=false "SELECT ticket_id, category, suggested_solution FROM \`${PROJECT_ID}.${DATASET_NAME}.ticket_resolutions\` LIMIT 15;"
  ```
- **Debugging:** Refer to `debug.md` for troubleshooting specific autograder failures.

## Part 4: Submission

**Checklist**

- Cloud Functions: `upload-kb`, `process-kb-document`, `publish-ticket`, `get-ticket-resolutions`
- BigQuery tables: `knowledge_chunks`, `ticket_resolutions`
- Pub/Sub: `support-tickets` topic and subscription
- Dataflow: `ticket-processor` job

Before submitting, run the self check script for sanity checks:

```bash
source gcloud_init.sh && bash self_check.sh
```

### Autograder

| Test      | What is checked                                              | Points  |
| --------- | ------------------------------------------------------------ | ------- |
| T1        | Upload 3 hidden KB documents via `upload_kb`                 | 10      |
| T2        | `retrieve_kb`: sentinel, random value, and source match      | 30      |
| T3        | Publish 5 hidden tickets via `publish_ticket`                | 10      |
| T4        | Resolution: ticket_id, suggested_solution, and random values | 50      |
| **Total** |                                                              | **100** |

> **Security Note:** All tests use hidden KB documents with randomly generated numeric facts unique to each grading run.
>
> **Sequential Dependency:** A test scoring 0 skips all subsequent tests (T1 → T2 → T3 → T4).

Submit using [submit.py](submit.py). Tests take less than 5 minutes. Real-time feedback will be provided by the autograder.

---

**Good luck!**
