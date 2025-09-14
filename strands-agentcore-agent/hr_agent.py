import json
import logging
import os
from typing import Dict, Any
import boto3
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
MODEL_ID = os.environ.get('MODEL_ID', 'us.anthropic.claude-3-5-sonnet-20241022-v2:0')
CANDIDATES_TABLE = os.environ.get('CANDIDATES_TABLE', 'hr-agents-candidates-agentcore')
DOCUMENTS_BUCKET = os.environ.get('DOCUMENTS_BUCKET', 'hr-agents-documents-agentcore')

# Initialize AgentCore app
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """AgentCore entrypoint for HR resume evaluation"""
    try:
        logger.info(f"🤖 AgentCore HR Agent - Processing payload: {payload}")
        
        # Extract parameters from payload
        bucket = payload.get('bucket', DOCUMENTS_BUCKET)
        resume_key = payload.get('resume_key')
        candidate_id = payload.get('candidate_id')
        
        if not resume_key:
            raise ValueError("resume_key is required in payload")
        
        # Process the resume using Strands multi-agent system
        result = process_resume_with_strands_agents(bucket, resume_key, candidate_id)
        
        return {
            "status": "success",
            "candidate_id": result.get('id'),
            "candidate_name": result.get('name'),
            "message": "Resume evaluation completed successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in AgentCore HR processing: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Resume evaluation failed"
        }

def process_resume_with_strands_agents(bucket: str, resume_key: str, candidate_id: str) -> Dict[str, Any]:
    """Process resume using Strands multi-agent collaboration"""
    try:
        # Download resume content
        resume_content = download_s3_file(bucket, resume_key)
        
        # Find matching job description
        job_content = find_job_description(bucket)
        
        # Create the HR Supervisor agent
        supervisor_agent = create_supervisor_agent()
        
        # Create evaluation request
        evaluation_request = f"""
        Please evaluate this candidate for the position using your specialized agent team.
        
        RESUME:
        {resume_content}
        
        JOB DESCRIPTION:
        {job_content}

        Work with your team to provide a comprehensive evaluation. Coordinate with:
        1. ResumeParserAgent to extract structured information
        2. JobAnalyzerAgent to analyze job requirements
        3. ResumeEvaluatorAgent to evaluate candidate fit
        4. GapIdentifierAgent to identify missing qualifications
        5. CandidateRaterAgent to provide numerical rating
        6. InterviewNotesAgent to generate interview materials

        Provide your final response as a comprehensive JSON structure.
        """
        
        # Execute evaluation
        logger.info("🤖 Starting AgentCore multi-agent evaluation...")
        evaluation_result = supervisor_agent(evaluation_request)
        logger.info("✅ AgentCore multi-agent evaluation completed")
        
        # Parse and structure the result
        structured_result = parse_evaluation_result(evaluation_result, candidate_id, resume_key, resume_content)
        
        # Store in DynamoDB
        store_candidate_evaluation(structured_result)
        
        return structured_result
        
    except Exception as e:
        logger.error(f"❌ Error in AgentCore processing: {str(e)}")
        raise

def create_supervisor_agent():
    """Create the HR Supervisor agent with specialized tools"""
    
    @tool
    def extract_resume_info(resume_text: str) -> str:
        """Extract structured information from resume text"""
        parser_agent = Agent(
            model=MODEL_ID,
            system_prompt="""You are a Resume Parser Agent specializing in extracting structured information from resumes.

Extract the following information:
1. Personal Information (name, contact, title, URLs)
2. Work Experience (companies, titles, dates, achievements, technologies)
3. Education (degrees, institutions, dates, coursework)
4. Skills (technical, soft skills, languages, proficiency)
5. Projects (names, descriptions, technologies, outcomes)

Structure your response as a JSON object with these categories."""
        )
        
        result = parser_agent(resume_text)
        return safe_extract_content(result)
    
    @tool
    def analyze_job_requirements(job_description: str) -> str:
        """Analyze job requirements"""
        analyzer_agent = Agent(
            model=MODEL_ID,
            system_prompt="""You are a Job Analyzer Agent specializing in extracting job requirements.

Analyze and extract:
1. Required Qualifications (education, experience, skills, certifications)
2. Preferred Qualifications (additional beneficial skills)
3. Technical Skills (languages, frameworks, tools, proficiency levels)
4. Company Culture (environment, values, work style)
5. Compensation and Benefits (if provided)

Structure your response as a JSON object with these categories."""
        )
        
        result = analyzer_agent(job_description)
        return safe_extract_content(result)
    
    @tool
    def evaluate_candidate_fit(resume_info: str, job_requirements: str) -> str:
        """Evaluate candidate fit"""
        evaluator_agent = Agent(
            model=MODEL_ID,
            system_prompt="""You are a Resume Evaluator Agent specializing in comparing candidates against job requirements.

Evaluate:
1. Skills Match Analysis (technical alignment, proficiency, missing skills)
2. Experience Relevance Assessment (industry, role similarity, years)
3. Education Fit Evaluation (degree requirements, certifications)
4. Project Relevance Review (scale, technology alignment)
5. Career Progression Analysis (growth trajectory, stability)

Structure your response as a JSON object with detailed analysis."""
        )
        
        evaluation_request = f"RESUME INFO:\n{resume_info}\n\nJOB REQUIREMENTS:\n{job_requirements}"
        result = evaluator_agent(evaluation_request)
        return safe_extract_content(result)

    @tool
    def identify_gaps(resume_info: str, job_requirements: str) -> str:
        """Identify gaps and inconsistencies"""
        gap_agent = Agent(
            model=MODEL_ID,
            system_prompt="""You are a Gap Identifier Agent specializing in finding gaps and inconsistencies.

Identify:
1. Missing Qualifications (required skills, education, experience)
2. Experience Gaps (timeline gaps, missing industry experience)
3. Skill Mismatches (outdated skills, missing proficiency)
4. Timeline Inconsistencies (overlapping dates, unexplained gaps)
5. Areas Needing Clarification (vague accomplishments, unclear levels)

Structure your response as a JSON object with specific examples."""
        )
        
        gap_request = f"RESUME INFO:\n{resume_info}\n\nJOB REQUIREMENTS:\n{job_requirements}"
        result = gap_agent(gap_request)
        return safe_extract_content(result)

    @tool
    def rate_candidate(resume_info: str, job_requirements: str, evaluation_info: str) -> str:
        """Rate candidate on 1-5 scale"""
        rater_agent = Agent(
            model=MODEL_ID,
            system_prompt="""You are a Candidate Rater Agent specializing in scoring candidates on a 1-5 scale.

Provide:
1. Overall Fit Score (1-5 scale with clear criteria)
2. Detailed Justification (evidence-based reasoning)
3. Strengths (key qualifications and achievements)
4. Weaknesses (missing qualifications and gaps)
5. Risk Assessment (likelihood of success, challenges)
6. Growth Potential (career trajectory, learning capacity)

Structure your response as a JSON object with numerical rating and analysis."""
        )
        
        rating_request = f"RESUME INFO:\n{resume_info}\n\nJOB REQUIREMENTS:\n{job_requirements}\n\nEVALUATION:\n{evaluation_info}"
        result = rater_agent(rating_request)
        return safe_extract_content(result)

    @tool
    def generate_interview_notes(resume_info: str, job_requirements: str) -> str:
        """Generate interview preparation materials"""
        interview_agent = Agent(
            model=MODEL_ID,
            system_prompt="""You are an Interview Notes Agent specializing in generating interview preparation materials.

Generate:
1. Technical Questions (skill verification, knowledge assessment)
2. Experience-Based Questions (project details, role scenarios)
3. Areas to Probe Deeper (unclear points, potential gaps)
4. Concerns to Address (gaps, inconsistencies, fit issues)
5. Behavioral Assessment (collaboration, problem-solving, communication)

Structure your response as a JSON object with specific, tailored questions."""
        )
        
        interview_request = f"RESUME INFO:\n{resume_info}\n\nJOB REQUIREMENTS:\n{job_requirements}"
        result = interview_agent(interview_request)
        return safe_extract_content(result)

    # Create the main HR Supervisor Agent
    supervisor_agent = Agent(
        model=MODEL_ID,
        tools=[
            extract_resume_info,
            analyze_job_requirements, 
            evaluate_candidate_fit,
            identify_gaps,
            rate_candidate,
            generate_interview_notes
        ],
        system_prompt="""You are the Supervisor Agent for HR resume evaluation running on Amazon Bedrock AgentCore Runtime.

Coordinate with your specialized team to provide comprehensive candidate evaluations:

1. Have ResumeParserAgent extract structured information from the resume
2. Have JobAnalyzerAgent analyze the job requirements
3. Have ResumeEvaluatorAgent evaluate candidate fit
4. Have GapIdentifierAgent identify missing qualifications
5. Have CandidateRaterAgent provide numerical rating (1-5 scale)
6. Have InterviewNotesAgent generate interview materials

CRITICAL: Output your final response as a valid JSON object in this exact format:

{
  "resume_parsing": {
    "analysis": "Detailed analysis",
    "personal_info": {"name": "Full Name", "email": "email", "phone": "phone", "location": "location"},
    "experience": [{"title": "Job Title", "company": "Company", "duration": "2020-2023", "achievements": []}],
    "education": [{"degree": "Degree", "institution": "University", "year": "2019"}],
    "skills": {"technical": [], "soft": []}
  },
  "job_analysis": {
    "analysis": "Detailed job analysis",
    "required_skills": [],
    "preferred_skills": [],
    "experience_level": "5+ years",
    "education_requirements": "Bachelor's degree"
  },
  "resume_evaluation": {
    "analysis": "Detailed evaluation",
    "skills_match_percentage": 85,
    "experience_relevance": "Highly relevant",
    "education_alignment": "Exceeds requirements"
  },
  "gap_analysis": {
    "analysis": "Detailed gap analysis",
    "missing_skills": [],
    "experience_gaps": [],
    "development_areas": []
  },
  "candidate_rating": {
    "rating": 4,
    "justification": "Detailed justification",
    "strengths": [],
    "weaknesses": []
  },
  "interview_notes": {
    "questions": [],
    "focus_areas": [],
    "talking_points": []
  }
}"""
    )
    
    return supervisor_agent

def safe_extract_content(result) -> str:
    """Extract text content from Strands agent response"""
    try:
        # Handle different response formats
        if hasattr(result, 'content') and isinstance(result.content, list):
            text_parts = []
            for item in result.content:
                if hasattr(item, 'text'):
                    text_parts.append(item.text)
                elif isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                else:
                    text_parts.append(str(item))
            return '\n'.join(text_parts)
        elif hasattr(result, 'content'):
            return str(result.content)
        elif hasattr(result, 'message'):
            return str(result.message)
        elif isinstance(result, dict):
            # Handle dict response format from AgentCore
            if 'role' in result and 'content' in result:
                content = result['content']
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(item['text'])
                        else:
                            text_parts.append(str(item))
                    return '\n'.join(text_parts)
                else:
                    return str(content)
            # Handle message format
            elif 'message' in result:
                message = result['message']
                if isinstance(message, dict) and 'content' in message:
                    content = message['content']
                    if isinstance(content, list):
                        text_parts = []
                        for item in content:
                            if isinstance(item, dict) and 'text' in item:
                                text_parts.append(item['text'])
                            else:
                                text_parts.append(str(item))
                        return '\n'.join(text_parts)
                    else:
                        return str(content)
                else:
                    return str(message)
            return str(result)
        else:
            return str(result)
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}")
        return str(result)

def parse_evaluation_result(evaluation_result, candidate_id: str, resume_key: str, resume_content: str) -> Dict[str, Any]:
    """Parse the evaluation result into structured format"""
    try:
        from datetime import datetime
        
        evaluation_content = safe_extract_content(evaluation_result)
        evaluation_json = safe_parse_json(evaluation_content)
        
        candidate_name = extract_name_from_key(resume_key)
        
        if evaluation_json and isinstance(evaluation_json, dict):
            if "resume_parsing" in evaluation_json and "personal_info" in evaluation_json["resume_parsing"]:
                candidate_name = evaluation_json["resume_parsing"]["personal_info"].get("name", candidate_name)
            
            result = {
                "id": candidate_id,
                "resume_key": resume_key,
                "name": candidate_name,
                "status": "completed",
                "created_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "evaluated_by": "Strands AgentCore Multi-Agent System",
                "resume_text": resume_content,
                
                # Store individual components as separate attributes
                "resume_parsing": evaluation_json.get("resume_parsing", {}),
                "job_analysis": evaluation_json.get("job_analysis", {}),
                "evaluation_results": evaluation_json.get("resume_evaluation", {}),
                "gaps_analysis": evaluation_json.get("gap_analysis", {}),
                "candidate_rating": evaluation_json.get("candidate_rating", {}),
                "interview_notes": evaluation_json.get("interview_notes", {}),
                
                # Keep metadata for debugging
                "agentcore_metadata": {
                    "runtime_platform": "Amazon Bedrock AgentCore",
                    "agent_framework": "Strands Agents SDK",
                    "model_used": MODEL_ID,
                    "raw_response": evaluation_content[:1000]  # Truncated for storage
                }
            }
            
            return result
        else:
            # Fallback structure
            return {
                "id": candidate_id,
                "resume_key": resume_key,
                "name": candidate_name,
                "status": "completed",
                "created_at": datetime.utcnow().isoformat(),
                "evaluated_by": "Strands AgentCore Multi-Agent System",
                "resume_text": resume_content,
                "agentcore_metadata": {
                    "runtime_platform": "Amazon Bedrock AgentCore",
                    "evaluation_content": evaluation_content
                }
            }
        
    except Exception as e:
        logger.error(f"Error parsing evaluation: {str(e)}")
        return {
            "id": candidate_id,
            "resume_key": resume_key,
            "name": extract_name_from_key(resume_key),
            "status": "error",
            "error": f"Parsing error: {str(e)}",
            "created_at": datetime.utcnow().isoformat(),
            "evaluated_by": "Strands AgentCore Multi-Agent System (Error)"
        }

def safe_parse_json(content: str) -> Dict[str, Any]:
    """Safely parse JSON from text content"""
    try:
        content = content.strip()
        
        # Handle escaped JSON strings first
        if '\\\"' in content:
            content = content.replace('\\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
        
        if content.startswith('{'):
            return json.loads(content)
        
        # Look for JSON in markdown code blocks
        import re
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        json_match = re.search(json_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if json_match:
            json_text = json_match.group(1).strip()
            if '\\\"' in json_text:
                json_text = json_text.replace('\\\"', '"').replace('\\n', '\n')
            return json.loads(json_text)
        
        # Look for JSON structure anywhere
        start_idx = content.find('{')
        if start_idx != -1:
            brace_count = 0
            end_idx = start_idx
            
            for i in range(start_idx, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if brace_count == 0:
                json_text = content[start_idx:end_idx]
                if '\\\"' in json_text:
                    json_text = json_text.replace('\\\"', '"').replace('\\n', '\n')
                return json.loads(json_text)
        
        return None
        
    except Exception as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return None

def download_s3_file(bucket: str, key: str) -> str:
    """Download file content from S3"""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        logger.error(f"Error downloading S3 file {key}: {str(e)}")
        raise

def find_job_description(bucket: str) -> str:
    """Find and download job description from S3"""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix='jobs/')
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            return "No specific job description found. Please evaluate general qualifications."
        
        job_key = response['Contents'][0]['Key']
        return download_s3_file(bucket, job_key)
        
    except Exception as e:
        logger.error(f"Error finding job description: {str(e)}")
        return "No job description available. Please evaluate general qualifications."

def extract_name_from_key(resume_key: str) -> str:
    """Extract candidate name from resume file key"""
    try:
        filename = resume_key.split('/')[-1]
        name = filename.replace('.txt', '').replace('_', ' ').replace('-', ' ')
        return ' '.join(word.capitalize() for word in name.split())
    except:
        return "Unknown Candidate"

def store_candidate_evaluation(evaluation_data: Dict[str, Any]) -> None:
    """Store evaluation data in DynamoDB"""
    try:
        from decimal import Decimal
        
        def convert_floats(obj):
            if isinstance(obj, dict):
                return {k: convert_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats(v) for v in obj]
            elif isinstance(obj, float):
                return Decimal(str(obj))
            else:
                return obj
        
        converted_data = convert_floats(evaluation_data)
        
        candidates_table = dynamodb.Table(CANDIDATES_TABLE)
        candidates_table.put_item(Item=converted_data)
        logger.info(f"✅ Stored evaluation for candidate: {evaluation_data.get('name', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"❌ Error storing evaluation in DynamoDB: {str(e)}")
        raise

if __name__ == "__main__":
    app.run()
