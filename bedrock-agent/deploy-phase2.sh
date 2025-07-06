#!/bin/bash

# Deploy Phase 2 of the HR AI Multi-Agent System

echo "🚀 Deploying HR AI Multi-Agent System - Phase 2"
echo "=============================================="

# Deploy the multi-agent stack phase 2 (configure collaborators)
echo "📦 Configuring Agent Collaborators (Phase 2)..."
sam deploy --template-file template-agents-phase2.yaml --stack-name bedrock-agent-phase2 --capabilities CAPABILITY_IAM --parameter-overrides Environment=dev --region us-east-1 --profile personal

if [ $? -ne 0 ]; then
    echo "❌ Failed to configure agent collaborators (Phase 2)"
    exit 1
fi

echo "✅ Agent collaborators configured successfully (Phase 2)"

echo ""
echo "🎉 Phase 2 deployment completed successfully!"
echo ""
echo "The system now has:"
echo "1. 🎯 Supervisor Agent - Configured with collaborators"
echo "2. 📋 Resume Parser Agent - Connected as collaborator"
echo "3. 🔍 Job Analyzer Agent - Connected as collaborator"
echo "4. ⚖️  Resume Evaluator Agent - Connected as collaborator"
echo "5. 🔎 Gap Identifier Agent - Connected as collaborator"
echo "6. ⭐ Candidate Rater Agent - Connected as collaborator"
echo "7. 📝 Interview Notes Agent - Connected as collaborator"
echo ""
echo "Next steps:"
echo "1. Deploy the Lambda stack using deploy-lambda.sh"
