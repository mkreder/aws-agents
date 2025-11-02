import json
import logging
import os
import uuid
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
agentcore_client = boto3.client('bedrock-agentcore')

# Environment variables
AGENT_ARN = os.environ['AGENT_ARN']
DOCUMENTS_BUCKET = os.environ['DOCUMENTS_BUCKET']

def lambda_handler(event, context):
    """
    Lambda handler for processing S3 events and invoking AgentCore agent.
    """
    try:
        logger.info(f"🔄 S3 Event Processor - Processing event: {event}")
        
        # Process each S3 record
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            # Only process resume files
            if not key.startswith('resumes/'):
                logger.info(f"⏭️ Skipping non-resume file: {key}")
                continue
            
            logger.info(f"🤖 Invoking AgentCore agent for resume: {key}")
            
            # Generate candidate ID
            candidate_id = str(uuid.uuid4())
            
            # Prepare payload for AgentCore agent
            payload = {
                "bucket": bucket,
                "resume_key": key,
                "candidate_id": candidate_id
            }
            
            # Invoke AgentCore agent
            result = invoke_agentcore_agent(payload)
            logger.info(f"✅ AgentCore processing completed: {result}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'S3 events processed successfully',
                'processed_files': len(event['Records'])
            })
        }
        
    except Exception as e:
        logger.error(f"❌ Error in S3 event processing: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'S3 event processing failed'
            })
        }

def invoke_agentcore_agent(payload):
    """
    Invoke the AgentCore agent with the given payload.
    """
    try:
        # Prepare the invocation request
        request = {
            'agentArn': AGENT_ARN,
            'payload': json.dumps(payload),
            'sessionId': str(uuid.uuid4())
        }
        
        logger.info(f"🚀 Invoking AgentCore agent: {AGENT_ARN}")
        
        # Invoke the agent
        response = agentcore_client.invoke_agent_runtime(**request)
        
        # Parse the response
        if 'payload' in response:
            result = json.loads(response['payload'])
            logger.info(f"✅ AgentCore agent response: {result}")
            return result
        else:
            logger.warning("No payload in AgentCore response")
            return {"status": "no_payload"}
        
    except Exception as e:
        logger.error(f"❌ Error invoking AgentCore agent: {str(e)}")
        raise
