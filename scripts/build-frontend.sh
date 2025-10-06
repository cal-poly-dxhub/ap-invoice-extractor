#!/bin/bash

# Build frontend for CDK deployment

set -e

echo "Building React frontend for CDK deployment..."

# Navigate to frontend directory
cd frontend

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "No package.json found. Checking for existing build..."
    if [ -d "build" ]; then
        echo "Using existing build directory"
        exit 0
    else
        echo "Error: No package.json and no build directory found"
        exit 1
    fi
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Build the React app
echo "Building React app..."
npm run build

echo "Frontend build completed successfully!"
echo "Build output is in: frontend/build"