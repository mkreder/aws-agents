#!/bin/bash

# Build the SAM application
echo "Building the SAM application..."
sam build

# Check if the build was successful
if [ $? -ne 0 ]; then
  echo "Failed to build the SAM application. Exiting."
  exit 1
fi

# Deploy the SAM application
echo "Deploying the SAM application..."
sam deploy --profile personal

# Check if the deployment was successful
if [ $? -ne 0 ]; then
  echo "Failed to deploy the SAM application. Exiting."
  exit 1
fi

# Upload sample files
echo "Uploading sample files..."
./upload_samples.py

echo "Deployment completed successfully!"