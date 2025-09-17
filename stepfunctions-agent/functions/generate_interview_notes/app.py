import json
import os
import boto3
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize clients
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
jobs_table = dynamodb.Table(os.environ.get('JOBS_TABLE', ''))
candidates_table = dynamodb.Table(os.environ.get('CANDIDATES_TABLE', ''))

# Model configuration
MODEL_ID = "us.amazon.nova-pro-v1:0"

def lambda_handler(event, context):
    """
    Generate interview preparation notes for a recruiter using Bedrock.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract data from the event
        resume_text = event.get('resume_text')
        candidate_id = event.get('candidate_id')
        candidate_name = event.get('name')
        evaluation = event.get('evaluation', {})
        gaps_analysis = event.get('gaps', {})
        rating = event.get('rating', {})
        job_title = event.get('job_title')
        
        if not resume_text or not candidate_id:
            raise ValueError("Missing required information in the event")
        
        # Get job description - required for proper interview preparation
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
        
        # Ensure we have a job description for proper interview preparation
        if not job_description:
            raise ValueError("Job description is required for interview notes generation")
        
        # Prepare prompt for Bedrock - always with job description
        prompt = f"""
        You are an expert HR assistant preparing interview notes for a recruiter, including:

        1. Suggested questions to assess the candidate's fit for the specific role
        2. Areas to probe deeper based on the resume analysis and job requirements
        3. Specific skills to verify during the interview that are critical for the role
        4. Potential concerns to address based on gaps or mismatches with the job requirements

        Generate:
        - Technical Questions: Specific technical questions based on their experience
        - Experience Questions: Questions about past experience relevant to the role
        - Behavioral Questions: Questions to assess soft skills and cultural fit
        - Project Deep-Dives: Questions about specific projects mentioned
        - Scenario Questions: Hypothetical situations relevant to the role
        - Clarification Questions: Areas needing more information or explanation
        - Strengths to Explore: Candidate's strong points to discuss further
        - Concerns to Address: Areas of concern that need clarification
        - Follow-up Actions: Next steps and additional assessments needed

        Tailor questions to the specific candidate and role requirements.
        Format your response as a JSON object with keys: technical_questions, experience_questions, skill_verification, concerns_to_address, general_notes.
        
        Job Description:
        {job_description}
        
        Resume:
        {resume_text}
        
        Candidate evaluation:
        {json.dumps(evaluation, indent=2)}
        
        Gaps analysis:
        {json.dumps(gaps_analysis, indent=2)}
        
        Candidate rating:
        {json.dumps(rating, indent=2)}
        """
        
        # Call Bedrock with the prompt
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1500,
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
        notes_text = response_body.get('content', [{}])[0].get('text', '')
        
        # Extract the JSON part from the response
        try:
            # Find JSON in the response
            start_idx = notes_text.find('{')
            end_idx = notes_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = notes_text[start_idx:end_idx]
                notes = json.loads(json_str)
            else:
                # If no JSON found, create a structured response
                notes = {
                    "technical_questions": ["See full interview notes text"],
                    "experience_questions": ["See full interview notes text"],
                    "skill_verification": ["See full interview notes text"],
                    "concerns_to_address": ["See full interview notes text"],
                    "general_notes": notes_text[:500] + "..." if len(notes_text) > 500 else notes_text
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, create a fallback structure
            notes = {
                "technical_questions": ["See full interview notes text"],
                "experience_questions": ["See full interview notes text"],
                "skill_verification": ["See full interview notes text"],
                "concerns_to_address": ["See full interview notes text"],
                "general_notes": notes_text[:500] + "..." if len(notes_text) > 500 else notes_text
            }
        
        # Add the raw notes text for reference
        notes['raw_notes'] = notes_text
        notes['job_title'] = job_title
        notes['candidate_name'] = candidate_name
        
        # Update the candidates table with all evaluation results and mark as completed
        try:
            candidates_table.update_item(
                Key={'id': candidate_id},
                UpdateExpression="""
                    SET #status = :status,
                        evaluation_results = :evaluation,
                        gaps_analysis = :gaps,
                        candidate_rating = :rating,
                        interview_notes = :notes,
                        completed_at = :completed_at,
                        job_title = :job_title
                """,
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':evaluation': evaluation,
                    ':gaps': gaps_analysis,
                    ':rating': rating,
                    ':notes': notes,
                    ':completed_at': datetime.utcnow().isoformat(),
                    ':job_title': job_title
                }
            )
            logger.info(f"Successfully updated candidate {candidate_id} status to completed")
        except Exception as e:
            logger.error(f"Error updating candidate status: {str(e)}")
            # Don't fail the function if DynamoDB update fails, but log the error
        
        logger.info(f"Successfully generated interview notes for candidate {candidate_id}")
        return notes
        
    except Exception as e:
        logger.error(f"Error generating interview notes: {str(e)}")
        raise e
