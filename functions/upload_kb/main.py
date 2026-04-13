import os
import functions_framework
from google.cloud import storage


@functions_framework.http
def upload_kb(request):
    """
    HTTP Cloud Function to upload a Knowledge Base document to GCS.

    Input:
        Multipart/form-data with a 'file' field containing the document.
        File will be uploaded using command:
        curl -X POST <FUNCTION_URL> -F "file=@<FILE_PATH>"

    Output (JSON):
        {
            "status": "success",
            "filename": "string"
        }
    """
    if request.method != "POST":
        return "Only POST requests are accepted", 405

    if "file" not in request.files:
        return "No file part in the request", 400

    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    bucket_name = os.environ.get("BUCKET_NAME")
    if not bucket_name:
        return "BUCKET_NAME environment variable not set", 500

    # TODO: Upload the file to the 'knowledge-base/' folder in Cloud Storage bucket
    # e.g. a local file "billing_information.md" -> gs://[BUCKET_NAME]/knowledge-base/billing_information.md

    return {"status": "success", "filename": file.filename}, 200
