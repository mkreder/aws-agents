#!/bin/bash

# Script to prepare all Bedrock agents after model update

REGION="us-east-1"

# Agent IDs
AGENT_IDS=(
    "ZYXYASYUW1"
    "VHZINNGW65"
    "QUL1FKTR4T"
    "CIZQX87PY3"
    "I6CPMMPZAE"
    "VGQI2BVUS8"
)

echo "🚀 Preparing all Bedrock agents..."
echo ""

for agent_id in "${AGENT_IDS[@]}"; do
    echo "📦 Preparing agent: $agent_id"
    
    aws bedrock-agent prepare-agent \
        --agent-id "$agent_id" \
        --region "$REGION" \
        --query '{agentId:agentId,status:agentStatus,version:agentVersion}' \
        --output table
    
    echo "✅ Prepared $agent_id"
    echo ""
done

echo "🎉 All agents prepared!"
