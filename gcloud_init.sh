#!/bin/bash
# Check if .env file exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  echo "✓ Environment variables loaded from .env"
else
  echo "✗ Error: .env file not found."
  return 1 2>/dev/null || exit 1
fi

# Set gcloud project
if [ ! -z "$PROJECT_ID" ]; then
  gcloud config set project $PROJECT_ID
  echo "✓ Project set to: $PROJECT_ID"
else
  echo "✗ Error: PROJECT_ID not set in .env"
fi

echo "✓ Configuration complete!"
