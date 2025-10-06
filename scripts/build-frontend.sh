#!/bin/bash

# Build frontend for CDK deployment

set -e

echo "Building React frontend for CDK deployment..."

# Navigate to frontend directory
cd ../invoiceable/frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Build the React app
echo "Building React app..."
npm run build

echo "Frontend build completed successfully!"
echo "Build output is in: ../invoiceable/frontend/build"