#!/bin/bash

# Strands Multi-Agent HR Resume Evaluation System Deployment Script
# This script deploys the complete system with infrastructure, Lambda functions, and Strands SDK packaging
# Updated: 2025-06-30 - Includes 15-minute timeout and structured JSON parsing

set -e

# Configuration
ENVIRONMENT=${ENVIRONMENT:-dev}
REGION=${REGION:-us-east-1}
MODEL_ID=${MODEL_ID:-us.anthropic.claude-3-7-sonnet-20250219-v1:0}

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Strands Multi-Agent HR Resume Evaluation System${NC}"
echo "=============================================================="
echo "Infrastructure Stack: strands-agent-infrastructure"
echo "Lambda Stack: strands-agent-lambda"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Model ID: $MODEL_ID"
echo ""

echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed${NC}"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo -e "${RED}❌ SAM CLI is not installed${NC}"
    exit 1
fi

# Check if Python and pip are available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo -e "${RED}❌ pip is not installed${NC}"
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed or not running${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

echo -e "${YELLOW}🏗️ Phase 1: Deploying Infrastructure (S3, DynamoDB)...${NC}"
sam deploy \
    --template-file template-infrastructure.yaml \
    --stack-name strands-agent-infrastructure \
    --region $REGION \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides Environment=$ENVIRONMENT \
    --resolve-s3 \
    --no-confirm-changeset

echo -e "${GREEN}✅ Infrastructure deployment completed${NC}"
echo ""

echo -e "${YELLOW}📦 Phase 2: Installing Strands SDK and Dependencies...${NC}"
# Clean up any existing dependencies
rm -rf packaging/_dependencies packaging/lambda
mkdir -p packaging/_dependencies packaging/lambda

echo "  🐳 Building Linux dependencies using Docker..."
# Build Docker image with Linux dependencies for x86_64 architecture
docker build --platform=linux/amd64 -f Dockerfile.deps -t strands-deps-x86 .

# Extract dependencies from Docker container
docker run --platform=linux/amd64 --rm -v $(pwd)/packaging:/output strands-deps-x86 sh -c "cp -r /build/dependencies/* /output/_dependencies/"

echo "  📁 Copying Lambda function code..."
cp functions/resume_processor/* packaging/lambda/

echo "  📦 Creating deployment packages..."
python3 create_lambda_package.py

# Verify packages were created
if [ ! -f "packaging/dependencies.zip" ]; then
    echo -e "${RED}❌ Dependencies package not found: packaging/dependencies.zip${NC}"
    exit 1
fi

if [ ! -f "packaging/app.zip" ]; then
    echo -e "${RED}❌ App package not found: packaging/app.zip${NC}"
    exit 1
fi

echo "  ✅ Verified deployment packages:"
echo "    - dependencies.zip ($(du -h packaging/dependencies.zip | cut -f1))"
echo "    - app.zip ($(du -h packaging/app.zip | cut -f1))"

echo -e "${GREEN}✅ Strands SDK packaging completed${NC}"
echo ""

echo -e "${YELLOW}🤖 Phase 3: Deploying Lambda Functions with Strands SDK...${NC}"
sam build --template-file template-lambda.yaml
sam deploy \
    --template-file template-lambda.yaml \
    --stack-name strands-agent-lambda \
    --region $REGION \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        Environment=$ENVIRONMENT \
        ModelId=$MODEL_ID \
        InfrastructureStackName=strands-agent-infrastructure \
    --resolve-s3 \
    --no-confirm-changeset

echo -e "${GREEN}✅ Lambda deployment completed${NC}"

# Verify layer attachment
echo -e "${YELLOW}🔍 Verifying layer attachment...${NC}"
FUNCTION_NAME="strands-agent-resume-processor-$ENVIRONMENT"
LAYER_INFO=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.Layers[0].Arn' --output text 2>/dev/null || echo "none")

if [ "$LAYER_INFO" != "none" ] && [ "$LAYER_INFO" != "None" ]; then
    echo "  ✅ Layer attached: $LAYER_INFO"
else
    echo -e "${RED}  ❌ No layer attached to function${NC}"
fi

echo ""

echo -e "${YELLOW}🔗 Phase 4: Configuring S3 Event Trigger...${NC}"
# Get bucket name and Lambda function ARN
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name strands-agent-infrastructure \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`DocumentsBucket`].OutputValue' \
    --output text)

LAMBDA_ARN=$(aws cloudformation describe-stacks \
    --stack-name strands-agent-lambda \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ResumeProcessorFunctionArn`].OutputValue' \
    --output text)

if [ -z "$BUCKET_NAME" ] || [ -z "$LAMBDA_ARN" ]; then
    echo -e "${RED}❌ Could not retrieve bucket name or Lambda ARN${NC}"
    exit 1
fi

echo "  🪣 Configuring S3 bucket: $BUCKET_NAME"
echo "  ⚡ Lambda function: $LAMBDA_ARN"

# Configure S3 event notification
aws s3api put-bucket-notification-configuration \
    --bucket $BUCKET_NAME \
    --notification-configuration '{
        "LambdaFunctionConfigurations": [
            {
                "Id": "StrandsResumeProcessorTrigger",
                "LambdaFunctionArn": "'$LAMBDA_ARN'",
                "Events": ["s3:ObjectCreated:*"],
                "Filter": {
                    "Key": {
                        "FilterRules": [
                            {
                                "Name": "prefix",
                                "Value": "resumes/"
                            }
                        ]
                    }
                }
            }
        ]
    }' \
    --region $REGION

echo -e "${GREEN}✅ S3 event trigger configured${NC}"
echo ""

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 System Information:${NC}"
echo "Bucket Name: $BUCKET_NAME"
echo "Lambda Function: $LAMBDA_ARN"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
echo ""
echo -e "${BLUE}🔗 Useful Commands:${NC}"
echo "View logs: aws logs tail /aws/lambda/strands-agent-resume-processor-$ENVIRONMENT --region $REGION --follow"
echo "List candidates: aws dynamodb scan --table-name strands-agent-candidates-$ENVIRONMENT --region $REGION"
echo "Test upload: aws s3 cp ../samples/resumes/john_doe_ai_engineer.txt s3://$BUCKET_NAME/resumes/test-\$(date +%s).txt"
