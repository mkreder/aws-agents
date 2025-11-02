#!/bin/bash

# Delete the Lambda stack first (since it depends on the agents stack)
echo "Deleting Lambda stack..."
sam delete --stack-name bedrock-agent-lambda --region us-east-1 --no-prompts

# Delete the agents stack
echo "Deleting agents stack..."
sam delete --stack-name bedrock-agent-agents --region us-east-1 --no-prompts

echo "Cleanup completed!"