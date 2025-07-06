#!/bin/bash

# Delete the stack
echo "Deleting stepfunctions-agent stack..."
sam delete --stack-name stepfunctions-agent --region us-east-1 --no-prompts

echo "Cleanup completed!"