#!/bin/bash

# Complete HR Multi-Agent System Deployment Script
# This script deploys the entire system including multi-agent collaboration

set -e

# Configuration
PROFILE=${1:-personal}
REGION=${2:-us-east-1}
ENVIRONMENT=${3:-dev}

echo "🚀 Deploying Complete HR AI Multi-Agent System"
echo "=============================================="
echo "Using AWS Profile: $PROFILE"
echo "Using Region: $REGION"
echo "Using Environment: $ENVIRONMENT"
echo ""

# Phase 1: Deploy Bedrock Agents
echo "📦 PHASE 1: Deploying Bedrock Agents..."
sam deploy \
    --template-file template-agents-phase1.yaml \
    --stack-name bedrock-agent \
    --region $REGION \
    --profile $PROFILE \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides Environment=$ENVIRONMENT \
    --resolve-s3 \
    --no-confirm-changeset

if [ $? -ne 0 ]; then
    echo "❌ Failed to deploy Bedrock Agents (Phase 1)"
    exit 1
fi

echo "✅ Bedrock Agents deployed successfully"
echo ""

# Get agent IDs from the stack outputs
echo "📋 Getting agent IDs from stack outputs..."
SUPERVISOR_AGENT_ID=$(aws cloudformation describe-stacks \
    --stack-name bedrock-agent \
    --region $REGION \
    --profile $PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`SupervisorAgentId`].OutputValue' \
    --output text)

RESUME_PARSER_AGENT_ID=$(aws cloudformation describe-stacks \
    --stack-name bedrock-agent \
    --region $REGION \
    --profile $PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`ResumeParserAgentId`].OutputValue' \
    --output text)

JOB_ANALYZER_AGENT_ID=$(aws cloudformation describe-stacks \
    --stack-name bedrock-agent \
    --region $REGION \
    --profile $PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`JobAnalyzerAgentId`].OutputValue' \
    --output text)

RESUME_EVALUATOR_AGENT_ID=$(aws cloudformation describe-stacks \
    --stack-name bedrock-agent \
    --region $REGION \
    --profile $PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`ResumeEvaluatorAgentId`].OutputValue' \
    --output text)

CANDIDATE_RATER_AGENT_ID=$(aws cloudformation describe-stacks \
    --stack-name bedrock-agent \
    --region $REGION \
    --profile $PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`CandidateRaterAgentId`].OutputValue' \
    --output text)

echo "Supervisor Agent ID: $SUPERVISOR_AGENT_ID"
echo "Resume Parser Agent ID: $RESUME_PARSER_AGENT_ID"
echo "Job Analyzer Agent ID: $JOB_ANALYZER_AGENT_ID"
echo "Resume Evaluator Agent ID: $RESUME_EVALUATOR_AGENT_ID"
echo "Candidate Rater Agent ID: $CANDIDATE_RATER_AGENT_ID"
echo ""

# Phase 2: Configure Multi-Agent Collaboration
echo "🤝 PHASE 2: Configuring Multi-Agent Collaboration..."

# First, update the Supervisor Agent to enable collaboration
echo "📝 Updating Supervisor Agent to enable collaboration..."
aws bedrock-agent update-agent \
    --agent-id $SUPERVISOR_AGENT_ID \
    --agent-name "bedrock-agent-supervisor-$ENVIRONMENT" \
    --foundation-model "amazon.nova-pro-v1:0" \
    --agent-collaboration "SUPERVISOR_ROUTER" \
    --agent-resource-role-arn "arn:aws:iam::$(aws sts get-caller-identity --profile $PROFILE --query Account --output text):role/bedrock-agent-BedrockAgentRole" \
    --instruction "You are the Supervisor Agent for HR resume evaluation. You coordinate with specialized collaborator agents to provide comprehensive candidate evaluations.

When a user requests resume evaluation, you MUST follow this workflow:
1. Use AgentCommunication__sendMessage to contact ResumeParserAgent to extract key information from the resume
2. Use AgentCommunication__sendMessage to contact JobAnalyzerAgent to analyze the job requirements
3. Use AgentCommunication__sendMessage to contact ResumeEvaluatorAgent to evaluate the candidate against job requirements
4. Use AgentCommunication__sendMessage to contact CandidateRaterAgent to get a numerical rating (1-5 scale)
5. Compile all results from your collaborators into a comprehensive evaluation report

You have access to these collaborator agents:
- ResumeParserAgent: Extracts structured information from resumes
- JobAnalyzerAgent: Analyzes job descriptions and requirements
- ResumeEvaluatorAgent: Evaluates candidate fit against job requirements
- CandidateRaterAgent: Provides numerical ratings with justification

ALWAYS delegate specific tasks to the appropriate collaborator agents using AgentCommunication__sendMessage. Do NOT attempt to do the specialized work yourself. Your role is to orchestrate the workflow and compile the final comprehensive report." \
    --region $REGION \
    --profile $PROFILE

echo "✅ Supervisor Agent collaboration enabled"
echo ""

# Function to get dev-alias ID for an agent
get_dev_alias_id() {
    local agent_id=$1
    aws bedrock-agent list-agent-aliases \
        --agent-id $agent_id \
        --region $REGION \
        --profile $PROFILE \
        --query 'agentAliasSummaries[?agentAliasName==`dev-alias`].agentAliasId' \
        --output text
}

# Get alias IDs
RESUME_PARSER_ALIAS_ID=$(get_dev_alias_id $RESUME_PARSER_AGENT_ID)
JOB_ANALYZER_ALIAS_ID=$(get_dev_alias_id $JOB_ANALYZER_AGENT_ID)
RESUME_EVALUATOR_ALIAS_ID=$(get_dev_alias_id $RESUME_EVALUATOR_AGENT_ID)
CANDIDATE_RATER_ALIAS_ID=$(get_dev_alias_id $CANDIDATE_RATER_AGENT_ID)

echo "Resume Parser Alias ID: $RESUME_PARSER_ALIAS_ID"
echo "Job Analyzer Alias ID: $JOB_ANALYZER_ALIAS_ID"
echo "Resume Evaluator Alias ID: $RESUME_EVALUATOR_ALIAS_ID"
echo "Candidate Rater Alias ID: $CANDIDATE_RATER_ALIAS_ID"
echo ""

# Associate collaborator agents with supervisor
echo "🔗 Associating collaborator agents with supervisor..."

# Resume Parser Agent
aws bedrock-agent associate-agent-collaborator \
    --agent-id $SUPERVISOR_AGENT_ID \
    --agent-version DRAFT \
    --collaborator-name "ResumeParserAgent" \
    --collaboration-instruction "Extract key information from resumes including personal details, skills, experience, education, and projects. Parse resume content and structure it for analysis." \
    --agent-descriptor aliasArn="arn:aws:bedrock:$REGION:$(aws sts get-caller-identity --profile $PROFILE --query Account --output text):agent-alias/$RESUME_PARSER_AGENT_ID/$RESUME_PARSER_ALIAS_ID" \
    --region $REGION \
    --profile $PROFILE

# Job Analyzer Agent
aws bedrock-agent associate-agent-collaborator \
    --agent-id $SUPERVISOR_AGENT_ID \
    --agent-version DRAFT \
    --collaborator-name "JobAnalyzerAgent" \
    --collaboration-instruction "Analyze job descriptions and extract key requirements including required skills, preferred skills, experience level, education requirements, and responsibilities." \
    --agent-descriptor aliasArn="arn:aws:bedrock:$REGION:$(aws sts get-caller-identity --profile $PROFILE --query Account --output text):agent-alias/$JOB_ANALYZER_AGENT_ID/$JOB_ANALYZER_ALIAS_ID" \
    --region $REGION \
    --profile $PROFILE

# Resume Evaluator Agent
aws bedrock-agent associate-agent-collaborator \
    --agent-id $SUPERVISOR_AGENT_ID \
    --agent-version DRAFT \
    --collaborator-name "ResumeEvaluatorAgent" \
    --collaboration-instruction "Evaluate resumes against job requirements analyzing skills match, experience relevance, education fit, and provide detailed assessment of candidate suitability." \
    --agent-descriptor aliasArn="arn:aws:bedrock:$REGION:$(aws sts get-caller-identity --profile $PROFILE --query Account --output text):agent-alias/$RESUME_EVALUATOR_AGENT_ID/$RESUME_EVALUATOR_ALIAS_ID" \
    --region $REGION \
    --profile $PROFILE

# Candidate Rater Agent
aws bedrock-agent associate-agent-collaborator \
    --agent-id $SUPERVISOR_AGENT_ID \
    --agent-version DRAFT \
    --collaborator-name "CandidateRaterAgent" \
    --collaboration-instruction "Provide numerical ratings (1-5 scale) for candidates based on their qualifications, experience, and fit for the role with detailed justification." \
    --agent-descriptor aliasArn="arn:aws:bedrock:$REGION:$(aws sts get-caller-identity --profile $PROFILE --query Account --output text):agent-alias/$CANDIDATE_RATER_AGENT_ID/$CANDIDATE_RATER_ALIAS_ID" \
    --region $REGION \
    --profile $PROFILE

echo "✅ Collaborator agents associated successfully"
echo ""

# Prepare the Supervisor Agent
echo "⚙️ Preparing Supervisor Agent..."
aws bedrock-agent prepare-agent \
    --agent-id $SUPERVISOR_AGENT_ID \
    --region $REGION \
    --profile $PROFILE

echo "✅ Supervisor Agent prepared successfully"
echo ""

# Wait for agent to be ready
echo "⏳ Waiting for Supervisor Agent to be ready..."
sleep 30

# Phase 3: Deploy Lambda Functions
echo "📦 PHASE 3: Deploying Lambda Functions..."
sam deploy \
    --template-file template-lambda.yaml \
    --stack-name bedrock-agent-lambda \
    --region $REGION \
    --profile $PROFILE \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides Environment=$ENVIRONMENT AgentsStackName=bedrock-agent \
    --resolve-s3 \
    --no-confirm-changeset

if [ $? -ne 0 ]; then
    echo "❌ Failed to deploy Lambda Functions"
    exit 1
fi

echo "✅ Lambda Functions deployed successfully"
echo ""

# Phase 4: Upload Sample Data
echo "📄 PHASE 4: Uploading Sample Data..."
python upload_samples.py --stack-name bedrock-agent-lambda

if [ $? -ne 0 ]; then
    echo "❌ Failed to upload sample data"
    exit 1
fi

echo "✅ Sample data uploaded successfully"
echo ""

echo "🎉 Complete HR Multi-Agent System Deployment Successful!"
echo "======================================================="
echo ""
echo "📋 System Components:"
echo "- Supervisor Agent ID: $SUPERVISOR_AGENT_ID"
echo "- Resume Parser Agent ID: $RESUME_PARSER_AGENT_ID"
echo "- Job Analyzer Agent ID: $JOB_ANALYZER_AGENT_ID"
echo "- Resume Evaluator Agent ID: $RESUME_EVALUATOR_AGENT_ID"
echo "- Candidate Rater Agent ID: $CANDIDATE_RATER_AGENT_ID"
echo ""
echo "🚀 Ready to process resumes!"
echo "Upload resumes to the S3 bucket 'resumes/' prefix to trigger evaluation."
echo ""
