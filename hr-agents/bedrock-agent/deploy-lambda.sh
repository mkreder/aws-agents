#!/bin/bash

# Deploy the Lambda stack for the HR AI Multi-Agent System

echo "🚀 Deploying HR AI Multi-Agent System - Lambda Stack"
echo "=================================================="

# Deploy the Lambda stack
echo "📦 Deploying Lambda stack for multi-agent system..."
sam deploy --config-file samconfig-lambda.toml --profile personal

if [ $? -ne 0 ]; then
    echo "❌ Failed to deploy Lambda stack"
    exit 1
fi

echo "✅ Lambda stack deployed successfully"

echo ""
echo "🎉 Lambda stack deployment completed successfully!"
echo ""
echo "The system now includes:"
echo "1. 📥 S3 Bucket - For storing resumes and job descriptions"
echo "2. 🔄 Resume Processor Lambda - Processes uploaded resumes"
echo ""
echo "Next steps:"
echo "1. Upload sample files using: ./upload_samples.py --stack-name bedrock-agent-lambda"
echo "2. Upload a resume to the S3 bucket in the 'resumes/' prefix to test the workflow"
echo "3. Check CloudWatch logs for the multi-agent evaluation results"
