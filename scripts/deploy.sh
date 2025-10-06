#!/bin/bash

# Invoice Processor CDK Deployment Script

set -e

echo "Starting Invoice Processor deployment..."

# Check if environment is set
ENVIRONMENT=${ENVIRONMENT:-dev}
echo "Deploying to environment: $ENVIRONMENT"

# Install CDK dependencies
echo "Installing CDK dependencies..."
pip install -r requirements.txt

# Build frontend
echo "Building frontend..."
./scripts/build-frontend.sh

# Bootstrap CDK (only needed once per account/region)
echo "Bootstrapping CDK..."
cdk bootstrap

# Deploy the stack
echo "Deploying Invoice Processor stack..."
cdk deploy --require-approval never --outputs-file outputs.json

# Extract API URL from outputs
API_URL=$(python3 -c "import json; data=json.load(open('outputs.json')); print(list(data.values())[0]['ApiUrl'])")
echo "API Gateway URL: $API_URL"

# Update frontend configuration
echo "Updating frontend API configuration..."
cat > "../invoiceable/frontend/.env" << EOF
REACT_APP_API_URL=$API_URL
REACT_APP_ENVIRONMENT=production
EOF

# Rebuild frontend with new API URL
echo "Rebuilding frontend with API URL..."
./scripts/build-frontend.sh

# Redeploy with updated frontend
echo "Redeploying with updated frontend..."
cdk deploy --require-approval never

echo "Deployment completed successfully!"
echo ""
echo "Application URLs:"
echo "Frontend: Check CloudFront URL in AWS Console outputs"
echo "API: $API_URL"