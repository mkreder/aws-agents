#!/bin/bash

# HR Agents - Strands AgentCore Implementation Deployment Script
set -e

ENVIRONMENT="agentcore"
STACK_NAME="hr-agents-strands-${ENVIRONMENT}"
REGION=${AWS_DEFAULT_REGION:-us-west-2}

echo "🚀 Deploying HR Agents - Strands AgentCore Implementation"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Stack: $STACK_NAME"

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is required but not installed"
    exit 1
fi

# Check Python and pip
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check required packages
echo "📦 Installing required packages..."
pip install --upgrade pip
pip install bedrock-agentcore strands-agents bedrock-agentcore-starter-toolkit boto3

# Step 1: Deploy infrastructure
echo "🏗️ Step 1: Deploying infrastructure..."
aws cloudformation deploy \
    --template-file template-infrastructure.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides Environment=$ENVIRONMENT \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION

# Get infrastructure outputs
echo "📋 Getting infrastructure outputs..."
DOCUMENTS_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`DocumentsBucket`].OutputValue' \
    --output text)

CANDIDATES_TABLE=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`CandidatesTable`].OutputValue' \
    --output text)

EXECUTION_ROLE=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`AgentCoreExecutionRole`].OutputValue' \
    --output text)

echo "✅ Infrastructure deployed:"
echo "  Documents Bucket: $DOCUMENTS_BUCKET"
echo "  Candidates Table: $CANDIDATES_TABLE"
echo "  Execution Role: $EXECUTION_ROLE"

# Step 2: Configure AgentCore
echo "🤖 Step 2: Configuring AgentCore agent..."

# Set environment variables for the agent
export CANDIDATES_TABLE=$CANDIDATES_TABLE
export DOCUMENTS_BUCKET=$DOCUMENTS_BUCKET

# Configure the agent using starter toolkit with execution role
echo "Configuring AgentCore with execution role: $EXECUTION_ROLE"
agentcore configure \
    --entrypoint hr_agent.py \
    --name "hr_agent_${ENVIRONMENT}" \
    --region $REGION \
    --execution-role $EXECUTION_ROLE \
    --ecr-repository-uri "" \
    --non-interactive

echo "✅ AgentCore configuration completed"

# Step 3: Deploy agent to AgentCore Runtime
echo "🚀 Step 3: Deploying agent to AgentCore Runtime..."
agentcore launch

# Get agent ARN from configuration
if [ -f "bedrock_agentcore.yaml" ]; then
    AGENT_ARN=$(grep -A 10 "bedrock_agentcore:" bedrock_agentcore.yaml | grep "arn:" | awk '{print $2}' | tr -d '"')
    echo "✅ Agent deployed with ARN: $AGENT_ARN"
else
    echo "❌ Could not find bedrock_agentcore.yaml configuration file"
    exit 1
fi

# Step 4: Update Lambda function with agent ARN
echo "🔧 Step 4: Updating Lambda function with agent ARN..."

# Update the Lambda function environment variables
aws lambda update-function-configuration \
    --function-name "hr-agents-s3-processor-${ENVIRONMENT}" \
    --environment Variables="{DOCUMENTS_BUCKET=$DOCUMENTS_BUCKET,AGENT_ARN=$AGENT_ARN}" \
    --region $REGION

echo "✅ Lambda function updated with agent ARN"

# Step 5: Test the deployment
echo "🧪 Step 5: Testing the deployment..."

# Test the AgentCore agent directly
echo "Testing AgentCore agent..."
agentcore invoke '{"bucket": "'$DOCUMENTS_BUCKET'", "resume_key": "test/sample.txt", "candidate_id": "test-123"}'

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Summary:"
echo "  Environment: $ENVIRONMENT"
echo "  Region: $REGION"
echo "  Documents Bucket: $DOCUMENTS_BUCKET"
echo "  Candidates Table: $CANDIDATES_TABLE"
echo "  Agent ARN: $AGENT_ARN"
echo ""
echo "📝 Next steps:"
echo "  1. Upload job descriptions to s3://$DOCUMENTS_BUCKET/jobs/"
echo "  2. Upload resumes to s3://$DOCUMENTS_BUCKET/resumes/"
echo "  3. Check results in DynamoDB table: $CANDIDATES_TABLE"
echo ""
echo "🔍 Monitoring:"
echo "  - AgentCore Observability: AWS Console > Bedrock > AgentCore"
echo "  - CloudWatch Logs: /aws/lambda/hr-agents-s3-processor-${ENVIRONMENT}"
echo "  - DynamoDB: $CANDIDATES_TABLE"
