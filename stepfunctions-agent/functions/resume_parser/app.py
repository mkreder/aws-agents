import json
import os
import boto3
import uuid
import logging
from urllib.parse import unquote_plus

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
candidates_table = dynamodb.Table(os.environ.get('CANDIDATES_TABLE'))
sfn_client = boto3.client('stepfunctions')

def lambda_handler(event, context):
    """
    Parse resume from S3 and extract key information.
    Triggered when a new resume is uploaded to the S3 bucket.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Get the S3 bucket and key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = unquote_plus(event['Records'][0]['s3']['object']['key'])
        
        # Only process files in the resumes/ prefix
        if not key.startswith('resumes/'):
            logger.info(f"Skipping file not in resumes/ prefix: {key}")
            return
        
        # Generate a unique ID for the candidate
        candidate_id = str(uuid.uuid4())
        
        # Get the resume content from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        resume_text = response['Body'].read().decode('utf-8')
        
        # Extract filename (candidate name) from the key
        filename = key.split('/')[-1]
        candidate_name = filename.replace('_resume.txt', '').replace('_', ' ').title()
        
        # Store basic information in DynamoDB
        candidate_item = {
            'id': candidate_id,
            'name': candidate_name,
            'resume_key': key,
            'resume_text': resume_text,
            'status': 'processing'
        }
        
        candidates_table.put_item(Item=candidate_item)
        
        # Prepare input for Step Functions
        step_function_input = {
            'candidate_id': candidate_id,
            'resume_text': resume_text,
            'name': candidate_name
        }
        
        # Start Step Functions execution
        state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
        if state_machine_arn:
            execution_name = f"resume-{candidate_id}"
            sfn_client.start_execution(
                stateMachineArn=state_machine_arn,
                name=execution_name,
                input=json.dumps(step_function_input)
            )
            logger.info(f"Started Step Functions execution: {execution_name}")
        else:
            logger.error("STATE_MACHINE_ARN environment variable not set")
        
        return {
            'candidate_id': candidate_id,
            'resume_text': resume_text,
            'name': candidate_name
        }
        
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise e