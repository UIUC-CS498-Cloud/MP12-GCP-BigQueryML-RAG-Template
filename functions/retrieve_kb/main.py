import functions_framework
from google import genai
from google.genai.types import EmbedContentConfig
from google.cloud import bigquery
import os
import json

# Initialize clients
bq_client = bigquery.Client()
client = genai.Client(vertexai=True, location='us-central1')

EMBEDDING_MODEL = "text-embedding-004"
DATASET_NAME = os.environ.get('DATASET_NAME', 'support_analytics')

@functions_framework.http
def retrieve_kb(request):
    """
    HTTP Cloud Function to retrieve top N chunks for a query.
    
    Input (JSON):
        {
            "text": "query string",
            "n": 3
        }
        
    Output (JSON):
        {
            "chunks": [
                {
                    "text": "chunk text content",
                    "source": "filename.md",
                    "similarity": 0.85
                }
            ]
        }
    """
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    request_json = request.get_json(silent=True)
    if not request_json or 'text' not in request_json:
        return (json.dumps({"error": "Missing 'text' in request body"}), 400, headers)
    
    query_text = request_json['text']
    n = int(request_json.get('n', 3))
    
    # TODO: Implement Knowledge Base Retrieval
    # 1. Generate an embedding for the query_text using EMBEDDING_MODEL
    #    (task_type="RETRIEVAL_QUERY")
    # 2. Run a vector search against the BigQuery knowledge_chunks table
    #    - SQL: SELECT text, source_document, 1 - ML.DISTANCE(embedding, [query_embedding], 'COSINE') as similarity
    #    - FROM {bq_client.project}.{DATASET_NAME}.knowledge_chunks
    #    - ORDER BY similarity DESC LIMIT {n}
    # 3. Format and return the top N chunks as JSON
    
    chunks = [] # Placeholder
    return (json.dumps({"chunks": chunks}), 200, headers)
