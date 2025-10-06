#!/bin/bash

# Update frontend configuration with deployed API URL

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <api-gateway-url>"
    echo "Example: $0 https://abc123.execute-api.us-west-2.amazonaws.com/prod"
    exit 1
fi

API_URL=$1
FRONTEND_DIR="frontend"

echo "Updating frontend configuration..."
echo "API URL: $API_URL"

# Create .env file
cat > "$FRONTEND_DIR/.env" << EOF
REACT_APP_API_URL=$API_URL
REACT_APP_ENVIRONMENT=production
EOF

echo "Frontend configuration updated successfully!"
echo "File created: $FRONTEND_DIR/.env"