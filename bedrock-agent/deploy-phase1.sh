#!/bin/bash

# Deploy Phase 1 of the HR AI Multi-Agent System

echo "🚀 Deploying HR AI Multi-Agent System - Phase 1"
echo "=============================================="

# Deploy the multi-agent stack first (Phase 1)
echo "📦 Deploying Multi-Agent Bedrock Agents stack (Phase 1)..."
sam deploy --template-file template-agents-phase1.yaml --stack-name bedrock-agent --capabilities CAPABILITY_IAM --parameter-overrides Environment=dev --region us-east-1 --profile personal

if [ $? -ne 0 ]; then
    echo "❌ Failed to deploy multi-agent stack (Phase 1)"
    exit 1
fi

echo "✅ Multi-agent stack (Phase 1) deployed successfully"

echo ""
echo "🎉 Phase 1 deployment completed successfully!"
echo ""
echo "The system includes:"
echo "1. 🎯 Supervisor Agent - Created with collaboration disabled"
echo "2. 📋 Resume Parser Agent - Created with alias"
echo "3. 🔍 Job Analyzer Agent - Created with alias"
echo "4. ⚖️  Resume Evaluator Agent - Created with alias"
echo "5. 🔎 Gap Identifier Agent - Created with alias"
echo "6. ⭐ Candidate Rater Agent - Created with alias"
echo "7. 📝 Interview Notes Agent - Created with alias"
echo ""
echo "Next steps:"
echo "1. Run deploy-phase2.sh to configure agent collaborators"
echo "2. Deploy the Lambda stack using deploy-lambda.sh"
