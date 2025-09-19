#!/bin/bash

# Set AWS profile
export AWS_PROFILE=personal

# Agent IDs to clean up
AGENTS=(
  "TUT7V8JGYM"  # SupervisorAgent
  "6GPWEJVZ3T"  # JobAnalyzerAgent
  "ZSFY96QEOE"  # ResumeParserAgent
  "UMC2PHOFWZ"  # ResumeEvaluatorAgent
  "ZHCFSYTDOE"  # CandidateRaterAgent
)

echo "🧹 Cleaning up Bedrock agents..."

# Step 1: Delete all agent aliases
for agent_id in "${AGENTS[@]}"; do
  echo "📋 Getting aliases for agent $agent_id..."
  aliases=$(aws bedrock-agent list-agent-aliases --agent-id "$agent_id" --region us-east-1 --query 'agentAliasSummaries[].agentAliasId' --output text 2>/dev/null)

  if [ -n "$aliases" ] && [ "$aliases" != "None" ]; then
    for alias_id in $aliases; do
      echo "  🗑️  Deleting alias $alias_id..."
      aws bedrock-agent delete-agent-alias --agent-id "$agent_id" --agent-alias-id "$alias_id" --region us-east-1 >/dev/null 2>&1
    done
  fi
done

echo "⏳ Waiting for aliases to be deleted..."
sleep 10

# Step 2: Delete all agents
for agent_id in "${AGENTS[@]}"; do
  echo "🤖 Deleting agent $agent_id..."
  aws bedrock-agent delete-agent --agent-id "$agent_id" --region us-east-1 >/dev/null 2>&1
  if [ $? -eq 0 ]; then
    echo "  ✅ Agent $agent_id deleted successfully"
  else
    echo "  ❌ Failed to delete agent $agent_id (may already be deleted)"
  fi
done

echo "🗄️  Clearing DynamoDB table..."
aws dynamodb delete-table --table-name bedrock-agent-candidates-dev --region us-east-1 >/dev/null 2>&1

echo "✅ Bedrock agents cleanup completed!"