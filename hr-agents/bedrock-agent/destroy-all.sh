#!/bin/bash

# Complete HR Multi-Agent System Destruction Script
# This script destroys all resources in the correct order

set -e

# Configuration
PROFILE=${1:-personal}
REGION=${2:-us-east-1}

echo "🗑️ Destroying Complete HR AI Multi-Agent System"
echo "=============================================="
echo "Using AWS Profile: $PROFILE"
echo "Using Region: $REGION"
echo ""

# Phase 1: Delete Lambda Stack (depends on agents stack)
echo "🗑️ PHASE 1: Deleting Lambda Stack..."
aws cloudformation delete-stack \
    --stack-name bedrock-agent-lambda \
    --region $REGION \
    --profile $PROFILE

echo "⏳ Waiting for Lambda stack deletion..."
aws cloudformation wait stack-delete-complete \
    --stack-name bedrock-agent-lambda \
    --region $REGION \
    --profile $PROFILE

echo "✅ Lambda stack deleted successfully"
echo ""

# Phase 2: Delete Agents Stack
echo "🗑️ PHASE 2: Deleting Agents Stack..."
aws cloudformation delete-stack \
    --stack-name bedrock-agent \
    --region $REGION \
    --profile $PROFILE

echo "⏳ Waiting for Agents stack deletion..."
aws cloudformation wait stack-delete-complete \
    --stack-name bedrock-agent \
    --region $REGION \
    --profile $PROFILE

echo "✅ Agents stack deleted successfully"
echo ""

echo "🎉 Complete HR Multi-Agent System Destroyed Successfully!"
echo "======================================================="
echo ""
