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
jobs_table = dynamodb.Table(os.environ.get('JOBS_TABLE'))
bedrock_runtime = boto3.client('bedrock-runtime')

# Model configuration
MODEL_ID = "us.amazon.nova-pro-v1:0"

def lambda_handler(event, context):
    """
    Extract and analyze job description from S3.
    Triggered when a new job description is uploaded to the S3 bucket.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Get the S3 bucket and key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = unquote_plus(event['Records'][0]['s3']['object']['key'])
        
        # Only process files in the jobs/ prefix
        if not key.startswith('jobs/'):
            logger.info(f"Skipping file not in jobs/ prefix: {key}")
            return
        
        # Generate a unique ID for the job
        job_id = str(uuid.uuid4())
        
        # Get the job description content from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        job_text = response['Body'].read().decode('utf-8')
        
        # Extract job title from the filename
        filename = key.split('/')[-1]
        job_title = filename.replace('.txt', '').replace('_', ' ').title()
        
        # Analyze job description using Bedrock
        job_analysis = analyze_job_description(job_text)
        
        # Store enhanced job information in DynamoDB
        job_info = {
            'id': job_id,
            'title': job_title,
            'description_key': key,
            'description_text': job_text,
            'analysis': job_analysis
        }
        
        jobs_table.put_item(Item=job_info)
        
        logger.info(f"Successfully processed and analyzed job description: {job_title}")
        return {
            'job_id': job_id,
            'title': job_title,
            'analysis': job_analysis
        }
        
    except Exception as e:
        logger.error(f"Error processing job description: {str(e)}")
        raise e

def analyze_job_description(job_text):
    """
    Analyze job description using Bedrock to extract key requirements.
    """
    try:
        prompt = f"""
        You are an expert HR assistant specialized in analyzing job descriptions and extracting key requirements.

        When given a job description, extract and categorize:
        - Required Skills: Must-have technical and soft skills
        - Preferred Skills: Nice-to-have skills and experience
        - Experience Level: Years of experience required
        - Education Requirements: Degree requirements and preferred fields
        - Responsibilities: Key job responsibilities and duties
        - Company Culture: Work environment and team dynamics
        - Growth Opportunities: Career advancement and learning opportunities
        - Compensation: Salary range and benefits if mentioned
        - Location Requirements: Remote, hybrid, or on-site preferences

        Prioritize requirements by importance and provide clear categorization.
        Format your response as a JSON object with structured job requirement data.
        
        Job Description:
        {job_text}
        """
        
        # Call Bedrock with the prompt using Anthropic Messages API format
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        analysis_text = response_body.get('content', [{}])[0].get('text', '')
        
        # Try to parse as JSON, fallback to text if parsing fails
        try:
            analysis = json.loads(analysis_text)
        except json.JSONDecodeError:
            analysis = {"raw_analysis": analysis_text}
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing job description: {str(e)}")
        return {"error": str(e), "raw_text": job_text}
