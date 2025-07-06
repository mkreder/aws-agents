import json
import os
import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize Bedrock client
bedrock_runtime = boto3.client('bedrock-runtime')

# Model ID for Claude (or another appropriate model)
MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

def lambda_handler(event, context):
    """
    Identify gaps or inconsistencies in the resume using AWS Bedrock.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract resume text and previous evaluation from the event
        resume_text = event.get('resume_text')
        candidate_name = event.get('name')
        previous_evaluation = event.get('evaluation', {})
        
        if not resume_text:
            raise ValueError("No resume text provided in the event")
        
        # Prepare prompt for Bedrock
        prompt = f"""
        You are an expert HR assistant analyzing a candidate's resume to identify gaps or inconsistencies, focusing on:

        1. Employment gaps (periods without work)
        2. Frequent job changes or short tenures
        3. Unclear or vague descriptions of responsibilities
        4. Mismatches between claimed skills and demonstrated experience
        5. Inconsistencies in timeline or career progression
        6. Over-qualification: Potential concerns about being overqualified
        7. Under-qualification: Areas where candidate may lack sufficient experience
        8. Red Flags: Concerning patterns or information
        9. Missing Information: Important details not provided

        Provide constructive analysis and suggest areas for clarification during interviews.
        Format your response as a JSON object with keys: employment_gaps, job_stability_issues, vague_descriptions, skill_mismatches, timeline_inconsistencies, overall_concerns.
        
        Resume:
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
        gaps_text = response_body.get('content', [{}])[0].get('text', '')
        
        # Extract the JSON part from the response
        try:
            # Find JSON in the response
            json_start = gaps_text.find('{')
            json_end = gaps_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                gaps_json = json.loads(gaps_text[json_start:json_end])
            else:
                # If no JSON found, use the whole text as overall_concerns
                gaps_json = {
                    "employment_gaps": [],
                    "job_stability_issues": [],
                    "vague_descriptions": [],
                    "skill_mismatches": [],
                    "timeline_inconsistencies": [],
                    "overall_concerns": gaps_text
                }
        except json.JSONDecodeError:
            gaps_json = {
                "employment_gaps": [],
                "job_stability_issues": [],
                "vague_descriptions": [],
                "skill_mismatches": [],
                "timeline_inconsistencies": [],
                "overall_concerns": gaps_text
            }
        
        # Add the gaps analysis to the event data for the next step
        event.update({
            'gaps_analysis': gaps_json
        })
        
        return event
        
    except Exception as e:
        logger.error(f"Error identifying gaps in resume: {str(e)}")
        raise e