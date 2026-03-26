import os
import functions_framework
from google.cloud import bigquery


@functions_framework.http
def get_ticket_resolutions(request):
    """
    HTTP Cloud Function to retrieve ticket resolutions from BigQuery.

    Input (JSON):
        {
            "ticket_ids": ["id1", "id2"]
        }

    Output (JSON):
        A list of ticket resolution records, e.g.:
        [
            {
                "ticket_id": "...",
                "timestamp": "...",
                "customer_tier": "...",
                "subject": "...",
                "message": "...",
                "retrieved_kb_chunks": [...],
                "top_kb_source": "...",
                "category": "...",
                "priority": "...",
                "suggested_solution": "...",
                "kb_facts_used": [...],
                "retrieval_confidence": 0.0,
                "processing_time_ms": 0,
                "solution_contains_kb_keywords": false
            }
            ...
        ]
    """
    request_json = request.get_json(silent=True)

    if not request_json or "ticket_ids" not in request_json:
        return {"error": "Missing ticket_ids in request body"}, 400

    ticket_ids = request_json["ticket_ids"]
    if not isinstance(ticket_ids, list):
        return {"error": "ticket_ids must be a list"}, 400

    project_id = os.environ.get("PROJECT_ID")
    dataset_name = os.environ.get("DATASET_NAME")
    table_id = f"{project_id}.{dataset_name}.ticket_resolutions"

    # TODO: Implement BigQuery query to select all columns that matches `ticket_ids`
    #       and return as a list of JSON objects.

    return "[]", 200, {"Content-Type": "application/json"}
