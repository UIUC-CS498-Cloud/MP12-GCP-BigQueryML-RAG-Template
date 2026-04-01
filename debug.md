## Debugging Guide

Use this section when the autograder reports an error. Find the failing test, match the symptom, and follow the steps.

---

### T1 – upload_kb (10 pts)

**`upload_kb unreachable` / connection error / timeout**

- Check that the Cloud Function is deployed: `gcloud functions describe upload-kb --gen2 --region ${REGION}`
- Verify `--allow-unauthenticated` was set during deploy: `gcloud functions describe upload-kb --gen2 --region ${REGION} --format="value(serviceConfig.ingressSettings)"` (expect `ALLOW_ALL`)
- Re-deploy with the correct `--set-env-vars BUCKET_NAME=...`

**HTTP 400 "No file part"**

- Your function expects `multipart/form-data` with a field named `file`. Do not change the field name.

**HTTP 500**

- Check `BUCKET_NAME` env var: `gcloud functions describe upload-kb --gen2 --region ${REGION} --format="value(serviceConfig.environmentVariables)"`
- Check logs: `gcloud functions logs read upload-kb --gen2 --region ${REGION} --limit 20`

---

### T2 – retrieve_kb (30 pts)

This test uploads hidden KB documents and polls `retrieve_kb` to verify they are indexed and searchable.

**HTTP 500 from retrieve_kb**

- Check `DATASET_NAME` env var on the function.
- Verify the `knowledge_chunks` table exists and has rows:
  ```bash
  bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET_NAME}.knowledge_chunks\`"
  ```
- If count is 0, check `process_kb` logs for insertion errors.
- Vertex AI embedding API may be disabled: ensure `aiplatform.googleapis.com` is enabled.

**Empty `chunks` list / Hidden values not found**

- **`process_kb` trigger not configured** – The function must be triggered by `google.cloud.storage.object.v1.finalized` on `${BUCKET_NAME}`.
- **`process_kb` is crashing** – Check logs: `gcloud functions logs read process-kb-document --gen2 --region ${REGION} --limit 50`
- **Stale Data / Duplicate Chunks** – If the autograder runs multiple times, BigQuery may contain multiple versions of the same "hidden" document.
  - **Upsert Strategy:** Ensure `process_kb` deletes existing chunks for the same `source_document` before inserting.
- **Embedding quota** – Vertex AI `text-embedding-004` has quota limits. Wait and re-submit.

**`indexed but source mismatch` (3/10 points)**

- The autograder found the `sentinel` string but the `source` field in the response did not match the expected filename (e.g., `hidden_loyalty_12345.md`). Check `retrieve_kb/main.py` to ensure it returns the correct `source` field.

**Similarity scores not in [0,1]**

- Verify the SQL uses `1 - ML.DISTANCE(..., 'COSINE')` (cosine similarity, not raw distance).

---

### T3 – publish_ticket (10 pts)

**HTTP 500**

- Check `PROJECT_ID` and `TOPIC_NAME` env vars on the function.
- Verify the Pub/Sub topic exists: `gcloud pubsub topics list`
- If missing: `gcloud pubsub topics create support-tickets`

**`missing message_id or ticket_id`**

- The function must return `{"message_id": "...", "ticket_id": "..."}`.

---

### T4 – resolutions (50 pts)

This test polls `get_ticket_resolutions` until the hidden tickets are processed by Dataflow and verified.

**`No resolutions after 60s`**

- Check if Dataflow job is `Running`: `gcloud dataflow jobs list --region=${REGION} --filter="state=Running"`
- Check Pub/Sub subscription for backlog: `gcloud pubsub subscriptions describe support-tickets-sub`
- Check Dataflow logs for runtime errors (e.g., Gemini API key missing, BigQuery permission denied).

**`incomplete resolution – missing fields`**

- Each resolution must contain at least `ticket_id` and `suggested_solution`.

**`expected value not in solution`**

- Gemini is not correctly grounding the response using the hidden KB documents.
- Ensure the Dataflow pipeline:
  1. Performs a vector search using the ticket message.
  2. Includes the retrieved text in the Gemini prompt.
  3. Maps the LLM output to the BigQuery schema.

---

## Useful Commands

**BigQuery: List all source documents and chunk counts**

```bash
bq query --use_legacy_sql=false "
SELECT source_document, COUNT(*) as chunk_count
FROM \`${PROJECT_ID}.${DATASET_NAME}.knowledge_chunks\`
GROUP BY source_document
ORDER BY chunk_count DESC;"
```

**BigQuery: Delete "hidden" documents**

```bash
bq query --use_legacy_sql=false --destination_table=${DATASET_NAME}.knowledge_chunks --replace "
SELECT * FROM \`${PROJECT_ID}.${DATASET_NAME}.knowledge_chunks\`
WHERE NOT source_document LIKE 'hidden%';"
```

**Dataflow: Check if the streaming job is running**

```bash
gcloud dataflow jobs list --region=${REGION} --filter="state=Running"
```

**Pub/Sub: Check for unacknowledged messages (backlog)**

```bash
gcloud pubsub subscriptions describe support-tickets-sub --format="value(numUndeliveredMessages)"
```
