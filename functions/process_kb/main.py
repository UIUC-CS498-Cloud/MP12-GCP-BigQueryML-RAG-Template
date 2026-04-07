import functions_framework
from google.cloud import storage, bigquery
from google import genai
from google.genai.types import EmbedContentConfig
from typing import List
import io
import hashlib
import os

# Initialize clients
storage_client = storage.Client()
bq_client = bigquery.Client()

# Initialize Gemini client for Vertex AI
client = genai.Client(vertexai=True, location="us-central1")

EMBEDDING_MODEL = "text-embedding-004"
CHUNK_SIZE = 500  # characters per chunk
OVERLAP = 50  # character overlap between chunks
DATASET_NAME = os.environ.get("DATASET_NAME", "support_analytics")


def chunk_text(
    text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP
) -> List[str]:
    """
    TODO: Split text into overlapping chunks
    """
    return []


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    TODO: Get embeddings from Vertex AI using google-genai SDK
    Use the EMBEDDING_MODEL and client.models.embed_content.
    Consider batch processing (max 250 batch size per request).
    """
    return []


def infer_category(filename):
    """Infer category from filename"""
    filename_lower = filename.lower()
    if "refund" in filename_lower or "billing" in filename_lower:
        return "billing"
    elif "product" in filename_lower or "manual" in filename_lower:
        return "technical"
    elif "login" in filename_lower or "troubleshooting" in filename_lower:
        return "account"
    elif "shipping" in filename_lower:
        return "shipping"
    else:
        return "general"


@functions_framework.cloud_event
def process_kb_document(cloud_event):
    """
    Triggered when markdown or text file uploaded to knowledge-base/ folder.
    Chunks document, generates embeddings, stores in BigQuery.

    Input (CloudEvent):
        GCS Finalize event data: {"bucket": "...", "name": "..."}

    Output:
        None (Writes results to the BigQuery 'knowledge_chunks' table)
    """
    # Get file info from event
    data = cloud_event.data
    bucket_name = data["bucket"]
    file_name = data["name"]

    print(f"Processing {file_name} from {bucket_name}")

    # Only process .md or .txt files in knowledge-base/ folder
    if not file_name.startswith("knowledge-base/") or not (
        file_name.endswith(".md") or file_name.endswith(".txt")
    ):
        print("Skipping - not a KB markdown or text file")
        return

    # TODO: Implement the document processing pipeline
    # 1. Download file content from GCS as text
    # 2. Split the text into chunks using chunk_text()
    # 3. Generate embeddings for the chunks using get_embeddings()
    # 4. Prepare metadata (source_doc, category)
    # 5. Insert the chunk data (chunk_id, source_document, text, embedding, category) into BigQuery
    #    - Table ID format: {bq_client.project}.{DATASET_NAME}.knowledge_chunks
    #    - YOU MUST delete existing chunks with same `source_document` before inserting new ones (Upsert)

    pass
