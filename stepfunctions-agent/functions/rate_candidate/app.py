import json
import os
import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize clients
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
jobs_table = dynamodb.Table(os.environ.get('JOBS_TABLE', ''))

# Model configuration
MODEL_ID = "us.amazon.nova-pro-v1:0"

def lambda_handler(event, context):
    """
    Rate a candidate from 1-5 based on their resume and job requirements using Bedrock.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract data from the event
        resume_text = event.get('resume_text')
        candidate_id = event.get('candidate_id')
        evaluation = event.get('evaluation', {})
        gaps_analysis = event.get('gaps', {})
        job_title = event.get('job_title')
        
        if not resume_text:
            raise ValueError("No resume text provided in the event")
        
        # Get job description - required for proper rating
        job_description = None
        if jobs_table.table_name:
            try:
                # Scan for the most recent job
                response = jobs_table.scan(Limit=1)
                if response.get('Items'):
                    job = response['Items'][0]
                    job_description = job.get('description_text')
                    job_title = job.get('title')
                    logger.info(f"Found job description: {job_title}")
            except Exception as e:
                logger.warning(f"Error retrieving job description: {str(e)}")
        
        # Ensure we have a job description for proper rating
        if not job_description:
            raise ValueError("Job description is required for candidate rating")
        
        # Prepare prompt for Bedrock - always with job description
        prompt = f"""
        You are an expert HR assistant rating a candidate from 1 (poor fit) to 5 (excellent fit) based on their resume and job requirements.

        Rating Scale:
        - 5 (Exceptional): Exceeds all requirements, ideal candidate
        - 4 (Strong): Meets all requirements with additional strengths
        - 3 (Good): Meets most requirements, solid candidate
        - 2 (Fair): Meets some requirements, has potential with development
        - 1 (Poor): Does not meet key requirements

        Consider:
        - Technical Skills Match (25%)
        - Relevant Experience (25%)
        - Education and Certifications (15%)
        - Project Portfolio (15%)
        - Career Progression (10%)
        - Cultural Fit Indicators (10%)

        Provide the numerical rating with detailed justification explaining the reasoning behind the score.
        Format your response as a JSON object with keys: rating, reasoning, strengths, weaknesses, job_fit.
        
        Job Description:
        {job_description}
        
        Resume:
        {resume_text}
        
        Previous evaluation:
        {json.dumps(evaluation, indent=2)}
        
        Gaps analysis:
        {json.dumps(gaps_analysis, indent=2)}
        """
        
        # Call Bedrock with the prompt
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
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
        response_body = json.loads(response.get('body').read())
        rating_text = response_body.get('content', [{}])[0].get('text', '')
        
        # Extract the JSON part from the response
        try:
            # Find JSON in the response
            start_idx = rating_text.find('{')
            end_idx = rating_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = rating_text[start_idx:end_idx]
                rating = json.loads(json_str)
            else:
                # If no JSON found, create a structured response
                rating = {
                    "rating": 3,  # Default middle rating
                    "reasoning": rating_text[:300] + "..." if len(rating_text) > 300 else rating_text,
                    "strengths": ["Analysis provided in raw format"],
                    "weaknesses": ["See full rating text"],
                    "job_fit": "See full rating text"
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, create a fallback structure
            rating = {
                "rating": 3,  # Default middle rating
                "reasoning": rating_text[:300] + "..." if len(rating_text) > 300 else rating_text,
                "strengths": ["Analysis provided in raw format"],
                "weaknesses": ["See full rating text"],
                "job_fit": "See full rating text"
            }
        
        # Add the raw rating text for reference
        rating['raw_rating'] = rating_text
        rating['job_title'] = job_title
        
        logger.info(f"Successfully rated candidate {candidate_id}: {rating.get('rating', 'N/A')}")
        return rating
        
    except Exception as e:
        logger.error(f"Error rating candidate: {str(e)}")
        raise e
