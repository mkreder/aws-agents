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
MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

def lambda_handler(event, context):
    """
    Evaluate a candidate's resume against job requirements using Bedrock.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract resume text from the event
        resume_text = event.get('resume_text')
        candidate_id = event.get('candidate_id')
        
        if not resume_text:
            raise ValueError("No resume text provided in the event")
        
        # Get the most recent job description - required for evaluation
        job_description = None
        job_title = None
        
        if jobs_table.table_name:
            try:
                # Scan for the most recent job (in a real app, you'd have a better way to select the relevant job)
                response = jobs_table.scan(Limit=1)
                if response.get('Items'):
                    job = response['Items'][0]
                    job_description = job.get('description_text')
                    job_title = job.get('title')
                    logger.info(f"Found job description: {job_title}")
            except Exception as e:
                logger.warning(f"Error retrieving job description: {str(e)}")
        
        # Ensure we have a job description for proper evaluation
        if not job_description:
            raise ValueError("Job description is required for resume evaluation")
        
        # Prepare prompt for Bedrock - always with job description
        prompt = f"""
        You are an expert HR assistant analyzing a candidate's resume against job requirements.

        Your evaluation should cover:
        - Skills Match: How well candidate's skills align with job requirements
        - Experience Relevance: Relevance of work experience to the role
        - Education Fit: Educational background alignment with requirements
        - Project Relevance: How projects demonstrate required capabilities
        - Career Progression: Growth trajectory and advancement
        - Cultural Fit: Alignment with company values and culture
        - Technical Depth: Depth of technical expertise in required areas
        - Leadership Experience: Management and leadership capabilities
        - Problem-Solving: Evidence of analytical and problem-solving skills

        Provide detailed analysis with specific examples from the resume.
        Format your response as a JSON object with keys: skills_summary, technical_expertise, education_summary, experience_summary, job_match_analysis.
        
        Job Description:
        {job_description}
        
        Candidate Resume:
        {resume_text}
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
        evaluation_text = response_body.get('content', [{}])[0].get('text', '')
        
        # Extract the JSON part from the response
        try:
            # Find JSON in the response
            start_idx = evaluation_text.find('{')
            end_idx = evaluation_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = evaluation_text[start_idx:end_idx]
                evaluation = json.loads(json_str)
            else:
                # If no JSON found, create a structured response
                evaluation = {
                    "skills_summary": evaluation_text[:200] + "..." if len(evaluation_text) > 200 else evaluation_text,
                    "technical_expertise": "Analysis provided in raw format",
                    "education_summary": "See full evaluation text",
                    "experience_summary": "See full evaluation text",
                    "job_match_analysis": "See full evaluation text"
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, create a fallback structure
            evaluation = {
                "skills_summary": evaluation_text[:200] + "..." if len(evaluation_text) > 200 else evaluation_text,
                "technical_expertise": "Analysis provided in raw format",
                "education_summary": "See full evaluation text",
                "experience_summary": "See full evaluation text", 
                "job_match_analysis": "See full evaluation text"
            }
        
        # Add the raw evaluation text for reference
        evaluation['raw_evaluation'] = evaluation_text
        evaluation['job_title'] = job_title
        
        logger.info(f"Successfully evaluated resume for candidate {candidate_id}")
        return evaluation
        
    except Exception as e:
        logger.error(f"Error evaluating resume: {str(e)}")
        raise e
