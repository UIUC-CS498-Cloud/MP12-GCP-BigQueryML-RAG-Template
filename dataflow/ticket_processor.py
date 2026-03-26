import apache_beam as beam
from apache_beam.options.pipeline_options import (
    PipelineOptions,
    GoogleCloudOptions,
    StandardOptions,
    WorkerOptions,
    SetupOptions,
)
from google import genai
from google.genai.types import EmbedContentConfig
from google.cloud import bigquery
import json
import time
import re
import os
import argparse
import sys

# Constants
EMBEDDING_MODEL = "text-embedding-004"
LLM_MODEL = "gemini-2.5-flash"


class ProcessTicketWithRAG(beam.DoFn):
    """Process each ticket with RAG"""

    def __init__(self, project_id, dataset_name):
        self.project_id = project_id
        self.dataset_name = dataset_name

    def setup(self):
        """Initialize models (called once per worker)"""
        # TODO: Initialize Gemini client and BigQuery client
        # self.client = genai.Client(vertexai=True, location="us-central1")
        # self.bq_client = bigquery.Client(project=self.project_id)
        pass

    def process(self, element):
        """
        TODO: Implement the RAG processing logic for a single ticket
        1. Parse the ticket JSON from the Pub/Sub message (element)
        2. Generate an embedding for the ticket text (subject + message)
        3. Perform a vector search in BigQuery to find the top 3 relevant KB chunks
        4. Construct a prompt for Gemini that includes the KB context and ticket details
        5. Call Gemini to generate a suggested solution, category, and priority
        6. Parse the Gemini response (should be JSON)
        7. Construct and yield the final output record (matching table_schema)
        """

        # Example output structure:
        # yield {
        #     "ticket_id": "...",
        #     "timestamp": "...",
        #     "customer_tier": "...",
        #     "subject": "...",
        #     "message": "...",
        #     "retrieved_kb_chunks": [...],
        #     "top_kb_source": "...",
        #     "category": "...",
        #     "priority": "...",
        #     "suggested_solution": "...",
        #     "kb_facts_used": [...],
        #     "retrieval_confidence": 0.0,
        #     "processing_time_ms": 0,
        #     "solution_contains_kb_keywords": False,
        # }
        pass


def run_pipeline(argv=None):
    """Run the Dataflow pipeline"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset_name",
        default=os.environ.get("DATASET_NAME", "support_analytics"),
        help="BigQuery dataset name",
    )
    parser.add_argument(
        "--input_subscription",
        help="Pub/Sub subscription to read from. Format: projects/<PROJECT>/subscriptions/<SUBSCRIPTION>",
    )
    parser.add_argument(
        "--output_table",
        help="BigQuery table to write to. Format: <PROJECT>:<DATASET>.<TABLE>",
    )

    known_args, pipeline_args = parser.parse_known_args(argv)

    # Pipeline options
    options = PipelineOptions(pipeline_args)

    # Standard Options
    standard_options = options.view_as(StandardOptions)
    if not standard_options.runner:
        standard_options.runner = "DataflowRunner"
    standard_options.streaming = True

    # GCP Options
    gcp_options = options.view_as(GoogleCloudOptions)
    if not gcp_options.project:
        gcp_options.project = os.environ.get("PROJECT_ID")

    if not gcp_options.region:
        gcp_options.region = os.environ.get("REGION", "us-central1")

    bucket_name = os.environ.get("BUCKET_NAME")
    if bucket_name:
        if not gcp_options.temp_location:
            gcp_options.temp_location = f"gs://{bucket_name}/temp"
        if not gcp_options.staging_location:
            gcp_options.staging_location = f"gs://{bucket_name}/staging"

    # Worker Options
    worker_options = options.view_as(WorkerOptions)
    if not worker_options.num_workers:
        worker_options.num_workers = 1
    if not worker_options.max_num_workers:
        worker_options.max_num_workers = 3
    if not worker_options.machine_type:
        worker_options.machine_type = "e2-small"

    # Setup Options
    setup_options = options.view_as(SetupOptions)
    setup_options.save_main_session = True
    # If setup_file is not provided via CLI, use the default path
    if not setup_options.setup_file:
        setup_options.setup_file = "setup.py"

    project_id = gcp_options.project
    dataset_name = known_args.dataset_name
    input_subscription = (
        known_args.input_subscription
        or f"projects/{project_id}/subscriptions/support-tickets-sub"
    )
    output_table = (
        known_args.output_table or f"{project_id}:{dataset_name}.ticket_resolutions"
    )

    # BigQuery schema
    table_schema = {
        "fields": [
            {"name": "ticket_id", "type": "STRING"},
            {"name": "timestamp", "type": "TIMESTAMP"},
            {"name": "customer_tier", "type": "STRING"},
            {"name": "subject", "type": "STRING"},
            {"name": "message", "type": "STRING"},
            {
                "name": "retrieved_kb_chunks",
                "type": "RECORD",
                "mode": "REPEATED",
                "fields": [
                    {"name": "text", "type": "STRING"},
                    {"name": "source_document", "type": "STRING"},
                    {"name": "similarity_score", "type": "FLOAT64"},
                ],
            },
            {"name": "top_kb_source", "type": "STRING"},
            {"name": "category", "type": "STRING"},
            {"name": "priority", "type": "STRING"},
            {"name": "suggested_solution", "type": "STRING"},
            {"name": "kb_facts_used", "type": "STRING", "mode": "REPEATED"},
            {"name": "retrieval_confidence", "type": "FLOAT64"},
            {"name": "processing_time_ms", "type": "INT64"},
            {"name": "solution_contains_kb_keywords", "type": "BOOL"},
        ]
    }

    # Build pipeline
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read from Pub/Sub"
            >> beam.io.ReadFromPubSub(subscription=input_subscription)
            | "Process with RAG"
            >> beam.ParDo(ProcessTicketWithRAG(project_id, dataset_name))
            | "Write to BigQuery"
            >> beam.io.WriteToBigQuery(
                table=output_table,
                schema=table_schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
            )
        )


if __name__ == "__main__":
    run_pipeline(sys.argv)
