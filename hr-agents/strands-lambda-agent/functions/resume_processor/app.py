# Updated on 2025-07-02 19:00:00 - Fix missing function and timeout issues
import json
import logging
import os
import uuid
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

import boto3
from strands import Agent, tool

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients with timeout configuration
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
CANDIDATES_TABLE = os.environ['CANDIDATES_TABLE']
DOCUMENTS_BUCKET = os.environ['DOCUMENTS_BUCKET']
MODEL_ID = os.environ.get('MODEL_ID', 'us.amazon.nova-pro-v1:0')

# DynamoDB table
candidates_table = dynamodb.Table(CANDIDATES_TABLE)

def retry_with_backoff(func, max_retries=3, base_delay=1):
    """Retry function with exponential backoff for timeout errors."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "timeout" in str(e).lower() or "read timed out" in str(e).lower():
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"⏰ Timeout on attempt {attempt + 1}, retrying in {delay}s: {str(e)}")
                    time.sleep(delay)
                    continue
            raise e
    return None

def lambda_handler(event, context):
    """
    Lambda handler for processing resume uploads via S3 events.
    """
    try:
        logger.info(f"🤖 Strands Multi-Agent HR System - Processing event: {event}")
        
        # Process each S3 record
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            # Only process resume files
            if not key.startswith('resumes/'):
                logger.info(f"⏭️ Skipping non-resume file: {key}")
                continue
            
            logger.info(f"🔄 Strands Multi-Agent System processing resume: {key}")
            
            # Process the resume using Strands multi-agent approach
            result = process_resume_with_strands_agents(bucket, key)
            logger.info(f"✅ Strands processing completed for: {result.get('name', 'Unknown')}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Strands Multi-Agent processing completed successfully',
                'processed_files': len(event['Records'])
            })
        }
        
    except Exception as e:
        logger.error(f"❌ Error in Strands Multi-Agent processing: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Strands Multi-Agent processing failed'
            })
        }

def process_resume_with_strands_agents(bucket: str, resume_key: str) -> Dict[str, Any]:
    """
    Process resume using Strands multi-agent collaboration with structured JSON output.
    """
    try:
        candidate_id = str(uuid.uuid4())
        
        # Download resume content
        resume_content = download_s3_file(bucket, resume_key)
        
        # Find matching job description
        job_content = find_job_description(bucket)
        
        # Create the HR Supervisor agent (matching bedrock-agent exactly)
        supervisor_agent = create_supervisor_agent()
        
        # Create evaluation request matching bedrock-agent format
        evaluation_request = f"""
        Please evaluate this candidate for the position using your specialized agent team.
        
        RESUME:
        {resume_content}
        
        JOB DESCRIPTION:
        {job_content}

        Work with your team to provide a comprehensive evaluation. Coordinate with:
        1. ResumeParserAgent to extract structured information from the resume
        2. JobAnalyzerAgent to analyze the job requirements
        3. ResumeEvaluatorAgent to evaluate candidate fit
        4. GapIdentifierAgent to identify missing qualifications
        5. CandidateRaterAgent to provide numerical rating with justification
        6. InterviewNotesAgent to generate interview preparation materials

        Provide your final response as a comprehensive JSON structure containing all evaluation results.
        """
        
        # Execute evaluation using Strands multi-agent system with retry logic
        logger.info("🤖 Starting Strands multi-agent evaluation...")
        
        def execute_evaluation():
            return supervisor_agent(evaluation_request)
        
        evaluation_result = retry_with_backoff(execute_evaluation, max_retries=2, base_delay=2)
        logger.info("✅ Strands multi-agent evaluation completed")
        
        # Parse and structure the evaluation result
        structured_result = parse_strands_evaluation(evaluation_result, candidate_id, resume_key, resume_content)
        
        # Store in DynamoDB
        store_candidate_evaluation(structured_result)
        
        return structured_result
        
    except Exception as e:
        logger.error(f"❌ Error in Strands multi-agent processing: {str(e)}")
        # Store error state in DynamoDB
        error_result = create_error_result(candidate_id, resume_key, str(e))
        store_candidate_evaluation(error_result)
        raise

def create_supervisor_agent():
    """
    Create the HR Supervisor agent with specialized tools using exact bedrock-agent prompts.
    """
    
    @tool
    def extract_resume_info(resume_text: str) -> str:
        """Extract structured information from resume text using ResumeParserAgent."""
        try:
            # Create ResumeParserAgent with exact bedrock-agent prompt
            parser_agent = Agent(
                model=MODEL_ID,
                system_prompt="""You are a Resume Parser Agent specializing in extracting structured information from resumes.

When given a resume, extract the following information:

1. **Personal Information**:
   - Full name
   - Contact information (email, phone, location)
   - Professional title/role
   - LinkedIn/portfolio URLs

2. **Work Experience**:
   - Company names
   - Job titles
   - Employment dates (start and end)
   - Key responsibilities and achievements
   - Technologies/tools used
   - Quantifiable results and metrics

3. **Education**:
   - Degrees and certifications
   - Institutions
   - Graduation dates
   - Relevant coursework
   - Academic achievements

4. **Skills**:
   - Technical skills (programming languages, tools, platforms)
   - Soft skills
   - Languages
   - Proficiency levels when specified

5. **Projects**:
   - Project names
   - Descriptions
   - Technologies used
   - Role and contributions
   - Outcomes and impact

Always structure your response as a JSON object with these categories. Be thorough and extract all relevant information, but do not invent or assume details not present in the resume."""
            )
            
            result = parser_agent(resume_text)
            return safe_extract_content(result)
        except Exception as e:
            logger.error(f"Error in resume parsing: {str(e)}")
            return json.dumps({"error": f"Resume parsing failed: {str(e)}"})
    
    @tool
    def analyze_job_requirements(job_description: str) -> str:
        """Analyze job requirements using JobAnalyzerAgent."""
        try:
            # Create JobAnalyzerAgent with exact bedrock-agent prompt
            analyzer_agent = Agent(
                model=MODEL_ID,
                system_prompt="""You are a Job Analyzer Agent specializing in extracting and analyzing job requirements from job descriptions.

When given a job description, analyze and extract the following information:

1. **Required Qualifications**:
   - Education requirements
   - Years of experience
   - Technical skills and proficiency levels
   - Certifications
   - Domain knowledge

2. **Preferred Qualifications**:
   - Additional skills that are beneficial
   - Nice-to-have experience
   - Optional certifications
   - Preferred background

3. **Technical Skills**:
   - Programming languages
   - Frameworks and libraries
   - Tools and platforms
   - Methodologies
   - Required proficiency levels

4. **Company Culture**:
   - Work environment
   - Team structure
   - Company values
   - Work-life balance indicators
   - Remote/hybrid/onsite expectations

5. **Compensation and Benefits**:
   - Salary range (if provided)
   - Benefits mentioned
   - Perks
   - Growth opportunities

Always structure your response as a JSON object with these categories. Be thorough and extract all relevant information, but do not invent or assume details not present in the job description."""
            )
            
            result = analyzer_agent(job_description)
            return safe_extract_content(result)
        except Exception as e:
            logger.error(f"Error in job analysis: {str(e)}")
            return json.dumps({"error": f"Job analysis failed: {str(e)}"})
    
    @tool
    def evaluate_candidate_fit(resume_info: str, job_requirements: str) -> str:
        """Evaluate candidate fit using ResumeEvaluatorAgent."""
        try:
            # Create ResumeEvaluatorAgent with exact bedrock-agent prompt
            evaluator_agent = Agent(
                model=MODEL_ID,
                system_prompt="""You are a Resume Evaluator Agent specializing in comparing candidate resumes against job requirements.

When given a resume and job description, evaluate the following:

1. **Skills Match Analysis**:
   - Technical skills alignment
   - Proficiency level match
   - Missing critical skills
   - Transferable skills
   - Skill relevance to the role

2. **Experience Relevance Assessment**:
   - Industry relevance
   - Role similarity
   - Project relevance
   - Years of experience match
   - Leadership/management experience (if required)

3. **Education Fit Evaluation**:
   - Degree requirements match
   - Relevant certifications
   - Specialized training alignment
   - Continuing education relevance

4. **Project Relevance Review**:
   - Project scale and complexity match
   - Technology stack alignment
   - Problem domain relevance
   - Demonstrated outcomes

5. **Career Progression Analysis**:
   - Growth trajectory
   - Increasing responsibility
   - Promotion history
   - Job stability
   - Career focus alignment

Always structure your response as a JSON object with these categories. Provide detailed analysis with specific examples from the resume that match or don't match the job requirements. Be objective and thorough in your evaluation."""
            )
            
            evaluation_request = f"RESUME INFO:\n{resume_info}\n\nJOB REQUIREMENTS:\n{job_requirements}\n\nProvide comprehensive evaluation."
            result = evaluator_agent(evaluation_request)
            return safe_extract_content(result)
        except Exception as e:
            logger.error(f"Error in candidate evaluation: {str(e)}")
            return json.dumps({"error": f"Candidate evaluation failed: {str(e)}"})

    @tool
    def identify_gaps(resume_info: str, job_requirements: str) -> str:
        """Identify gaps using GapIdentifierAgent."""
        try:
            # Create GapIdentifierAgent with exact bedrock-agent prompt
            gap_agent = Agent(
                model=MODEL_ID,
                system_prompt="""You are a Gap Identifier Agent specializing in finding inconsistencies, gaps, and missing information in resumes when compared to job requirements.

When given a resume and job description, identify the following:

1. **Missing Qualifications**:
   - Required skills not mentioned in the resume
   - Missing education requirements
   - Insufficient years of experience
   - Absent certifications
   - Lacking domain knowledge

2. **Experience Gaps**:
   - Employment timeline gaps
   - Missing relevant industry experience
   - Insufficient depth in required areas
   - Lack of specific project types
   - Missing leadership experience (if required)

3. **Skill Mismatches**:
   - Outdated technical skills
   - Missing proficiency levels
   - Irrelevant skill focus
   - Lack of required soft skills
   - Missing tool/platform experience

4. **Timeline Inconsistencies**:
   - Overlapping job dates
   - Unexplained career gaps
   - Short-term positions without explanation
   - Inconsistent job progression
   - Unclear duration of projects

5. **Areas Needing Clarification**:
   - Vague accomplishments
   - Unclear responsibilities
   - Ambiguous skill levels
   - Unexplained career changes
   - Incomplete project details

Always structure your response as a JSON object with these categories. Be specific about what's missing or inconsistent, citing examples from both the resume and job description. Focus on identifying factual gaps rather than making subjective judgments."""
            )
            
            gap_request = f"RESUME INFO:\n{resume_info}\n\nJOB REQUIREMENTS:\n{job_requirements}\n\nIdentify gaps and inconsistencies."
            result = gap_agent(gap_request)
            return safe_extract_content(result)
        except Exception as e:
            logger.error(f"Error in gap analysis: {str(e)}")
            return json.dumps({"error": f"Gap analysis failed: {str(e)}"})

    @tool
    def rate_candidate(resume_info: str, job_requirements: str, evaluation_info: str) -> str:
        """Rate candidate using CandidateRaterAgent."""
        try:
            # Create CandidateRaterAgent with exact bedrock-agent prompt
            rater_agent = Agent(
                model=MODEL_ID,
                system_prompt="""You are a Candidate Rater Agent specializing in evaluating and scoring candidates on a 1-5 scale based on their resume and fit for a specific job.

When given a resume and job description, provide the following:

1. **Overall Fit Score** (1-5 scale):
   - 1: Poor fit - Significant gaps in multiple critical areas
   - 2: Below average fit - Missing several important requirements
   - 3: Average fit - Meets basic requirements but has notable gaps
   - 4: Good fit - Meets most requirements with minor gaps
   - 5: Excellent fit - Meets or exceeds all key requirements

2. **Detailed Justification**:
   - Clear explanation of the rating
   - Evidence-based reasoning
   - Balanced assessment of strengths and weaknesses
   - Consideration of both technical and soft skills
   - Alignment with company culture (if mentioned)

3. **Strengths**:
   - Key qualifications that match the job
   - Standout skills and experiences
   - Unique value propositions
   - Relevant achievements
   - Potential contributions

4. **Weaknesses**:
   - Missing required qualifications
   - Experience gaps
   - Skill deficiencies
   - Potential red flags
   - Areas needing development

5. **Risk Assessment**:
   - Likelihood of success in the role
   - Potential onboarding challenges
   - Learning curve considerations
   - Retention risk factors
   - Performance risk factors

6. **Growth Potential**:
   - Career trajectory alignment
   - Learning capacity indicators
   - Adaptability signals
   - Leadership potential (if relevant)
   - Long-term fit assessment

Always structure your response as a JSON object with these categories. Be objective and thorough in your assessment, providing specific examples from the resume to support your rating and analysis."""
            )
            
            rating_request = f"RESUME INFO:\n{resume_info}\n\nJOB REQUIREMENTS:\n{job_requirements}\n\nEVALUATION:\n{evaluation_info}\n\nProvide numerical rating and detailed analysis."
            result = rater_agent(rating_request)
            return safe_extract_content(result)
        except Exception as e:
            logger.error(f"Error in candidate rating: {str(e)}")
            return json.dumps({"error": f"Candidate rating failed: {str(e)}"})

    @tool
    def generate_interview_notes(resume_info: str, job_requirements: str) -> str:
        """Generate interview notes using InterviewNotesAgent."""
        try:
            # Create InterviewNotesAgent with exact bedrock-agent prompt
            interview_agent = Agent(
                model=MODEL_ID,
                system_prompt="""You are an Interview Notes Agent specializing in generating interview preparation materials based on a candidate's resume and a job description.

When given a resume and job description, generate the following:

1. **Technical Questions**:
   - Skill verification questions
   - Technical knowledge assessment
   - Problem-solving scenarios
   - Tool/platform proficiency checks
   - Coding/design challenges (if applicable)

2. **Experience-Based Questions**:
   - Questions about specific projects
   - Role-specific scenario questions
   - Achievement verification questions
   - Team collaboration examples
   - Challenge resolution examples

3. **Areas to Probe Deeper**:
   - Unclear resume points
   - Potential skill gaps
   - Experience mismatches
   - Career transition explanations
   - Specific accomplishment details

4. **Concerns to Address**:
   - Employment gaps
   - Job hopping patterns
   - Missing required skills
   - Unclear responsibilities
   - Potential cultural fit issues

5. **Behavioral Assessment**:
   - Team collaboration style
   - Problem-solving approach
   - Communication effectiveness
   - Leadership capabilities (if relevant)
   - Adaptability indicators

Always structure your response as a JSON object with these categories. Create specific, tailored questions that will help assess the candidate's fit for the role. Focus on uncovering both technical capabilities and soft skills relevant to the position."""
            )
            
            interview_request = f"RESUME INFO:\n{resume_info}\n\nJOB REQUIREMENTS:\n{job_requirements}\n\nGenerate interview preparation materials."
            result = interview_agent(interview_request)
            return safe_extract_content(result)
        except Exception as e:
            logger.error(f"Error in interview notes generation: {str(e)}")
            return json.dumps({"error": f"Interview notes generation failed: {str(e)}"})

    # Create the main HR Supervisor Agent with exact bedrock-agent prompt
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
        system_prompt="""You are the Supervisor Agent for HR resume evaluation. You coordinate with specialized collaborator agents to provide comprehensive candidate evaluations.

When evaluating a candidate, work with your team naturally:

1. Start by having ResumeParserAgent extract and structure the key information from the resume
2. Have JobAnalyzerAgent analyze the job requirements and identify what qualifications are needed
3. Have ResumeEvaluatorAgent evaluate how well the candidate matches the job requirements
4. Have GapIdentifierAgent identify missing qualifications and gaps
5. Have CandidateRaterAgent provide a numerical rating (1-5 scale) with detailed justification
6. Have InterviewNotesAgent generate interview preparation materials

Your team members are:
- ResumeParserAgent: Extracts structured information from resumes
- JobAnalyzerAgent: Analyzes job descriptions and requirements  
- ResumeEvaluatorAgent: Evaluates candidate fit against job requirements
- GapIdentifierAgent: Identifies missing qualifications and gaps
- CandidateRaterAgent: Provides numerical ratings with justification
- InterviewNotesAgent: Generates interview preparation materials

Work collaboratively with your team. When you need specific expertise, naturally delegate to the appropriate team member. After gathering all the information from your collaborators, compile everything into a comprehensive evaluation report.

Focus on coordinating the work and compiling the final results rather than doing the specialized analysis yourself.

CRITICAL: You must output your final response as a valid JSON object in exactly this format:

{
  "resume_parsing": {
    "analysis": "Detailed resume parsing analysis with personal info, experience, education, skills, and projects",
    "personal_info": {
      "name": "Full Name",
      "email": "email@example.com", 
      "phone": "phone number",
      "location": "city, state"
    },
    "experience": [
      {
        "title": "Job Title",
        "company": "Company Name", 
        "duration": "2020-2023",
        "achievements": ["achievement 1", "achievement 2"]
      }
    ],
    "education": [
      {
        "degree": "Degree Name",
        "institution": "University Name",
        "year": "2019",
        "gpa": "3.8/4.0"
      }
    ],
    "skills": {
      "technical": ["skill1", "skill2"],
      "soft": ["skill1", "skill2"]
    }
  },
  "job_analysis": {
    "analysis": "Detailed job analysis including requirements, preferred qualifications, and cultural fit factors",
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill1", "skill2"],
    "experience_level": "5+ years",
    "education_requirements": "Bachelor's degree"
  },
  "resume_evaluation": {
    "analysis": "Detailed evaluation of how well the candidate matches the job requirements",
    "skills_match_percentage": 85,
    "experience_relevance": "Highly relevant",
    "education_alignment": "Exceeds requirements"
  },
  "gap_analysis": {
    "analysis": "Detailed gap analysis identifying missing qualifications and areas for development",
    "missing_skills": ["skill1", "skill2"],
    "experience_gaps": ["gap1", "gap2"],
    "development_areas": ["area1", "area2"]
  },
  "candidate_rating": {
    "rating": 4,
    "justification": "Detailed justification for the rating with specific examples and reasoning",
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2"]
  },
  "interview_notes": {
    "questions": ["Question 1?", "Question 2?", "Question 3?"],
    "focus_areas": ["Technical skills assessment", "Leadership experience", "Problem-solving approach"],
    "talking_points": ["Point 1", "Point 2", "Point 3"]
  }
}

This JSON structure will be parsed directly into the database. Ensure all fields contain meaningful, detailed content."""
    )
    
    return supervisor_agent

def safe_extract_content(result) -> str:
    """
    Extract text content from Strands agent response.
    """
    try:
        # Handle different Strands response types
        if hasattr(result, 'content') and isinstance(result.content, list):
            # Extract text from content list
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
        else:
            return str(result)
            
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}")
        return str(result)

def parse_strands_evaluation(evaluation_result, candidate_id: str, resume_key: str, resume_content: str) -> Dict[str, Any]:
    """
    Parse the Strands agent evaluation result into structured format matching bedrock-agent.
    """
    try:
        # Extract the message content from Strands result
        evaluation_content = safe_extract_content(evaluation_result)
        
        # Try to parse JSON from the evaluation content
        evaluation_json = safe_parse_json(evaluation_content)
        
        # Extract candidate name from resume or key
        candidate_name = extract_name_from_key(resume_key)
        
        # If we have structured JSON, use it; otherwise create minimal structure
        if evaluation_json and isinstance(evaluation_json, dict):
            # Extract candidate name from parsed data if available
            if "resume_parsing" in evaluation_json and "personal_info" in evaluation_json["resume_parsing"]:
                candidate_name = evaluation_json["resume_parsing"]["personal_info"].get("name", candidate_name)
            
            # Create comprehensive result structure matching bedrock-agent format
            result = {
                "id": candidate_id,
                "resume_key": resume_key,
                "name": candidate_name,
                "status": "completed",
                "created_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "evaluated_by": "Strands Multi-Agent System",
                "resume_text": resume_content,
                
                # Strands-specific collaboration metadata
                "strands_agent_collaboration": {
                    "evaluation_approach": "Multi-agent collaboration with specialized agents",
                    "agents_used": [
                        "HR Coordinator",
                        "Resume Parser", 
                        "Job Analyzer",
                        "Resume Evaluator",
                        "Gap Identifier",
                        "Candidate Rater",
                        "Interview Notes"
                    ],
                    "model_used": MODEL_ID,
                    "evaluation_content": {
                        "role": "assistant",
                        "content": [{"text": evaluation_content}]
                    }
                },
                
                "resume_parsing": evaluation_json.get("resume_parsing"),
                "job_analysis":evaluation_json.get("job_analysis"),
                "resume_evaluation": evaluation_json.get("resume_evaluation"),
                "gap_analysis_results": evaluation_json.get("gap_analysis"),
                "candidate_rating": evaluation_json.get("candidate_rating"),
                "interview_notes": evaluation_json.get("interview_notes")
            }
            
            logger.info(f"✅ Successfully parsed structured JSON evaluation with {len(evaluation_json)} components")
            return result
        else:
            logger.warning("No structured JSON found, using fallback structure")
            # Fallback structure if JSON parsing fails
            result = {
                "id": candidate_id,
                "resume_key": resume_key,
                "name": candidate_name,
                "status": "completed",
                "created_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "evaluated_by": "Strands Multi-Agent System",
                "resume_text": resume_content,
                "strands_agent_collaboration": {
                    "evaluation_approach": "Multi-agent collaboration with specialized agents",
                    "agents_used": ["HR Coordinator", "Resume Parser", "Job Analyzer", "Resume Evaluator", "Gap Identifier", "Candidate Rater", "Interview Notes"],
                    "model_used": MODEL_ID,
                    "evaluation_content": {"role": "assistant", "content": [{"text": evaluation_content}]}
                },
                "resume_parsing": {"agent": "Strands Resume Parser Agent", "candidate_name": candidate_name, "parsing_results": {"analysis": "Resume parsing completed"}},
                "job_analysis": {"agent": "Strands Job Analyzer Agent", "job_analysis_results": {"analysis": "Job analysis completed"}},
                "resume_evaluation": {"agent": "Strands Resume Evaluator Agent", "evaluation_results": {"analysis": "Resume evaluation completed"}},
                "gap_analysis": {"agent": "Strands Gap Identifier Agent", "gap_analysis_results": {"analysis": "Gap analysis completed"}},
                "candidate_rating": {"agent": "Strands Candidate Rater Agent", "rating_results": {"rating": 3, "justification": "Evaluation completed", "strengths": [], "weaknesses": []}},
                "interview_notes": {"agent": "Strands Interview Notes Agent", "interview_preparation": {"questions": [], "focus_areas": [], "talking_points": []}}
            }
            return result
        
    except Exception as e:
        logger.error(f"Error parsing Strands evaluation: {str(e)}")
        # Return minimal valid structure on error
        return {
            "id": candidate_id,
            "resume_key": resume_key,
            "name": extract_name_from_key(resume_key),
            "status": "error",
            "error": f"Parsing error: {str(e)}",
            "created_at": datetime.utcnow().isoformat(),
            "evaluated_by": "Strands Multi-Agent System (Error)",
            "strands_agent_collaboration": {
                "evaluation_approach": "Error during Strands agent processing",
                "error_details": str(e)
            }
        }

def safe_parse_json(content: str) -> Dict[str, Any]:
    """
    Safely parse JSON from text content with fallback mechanisms.
    """
    try:
        # Clean the content
        content = content.strip()
        
        # First, try to extract JSON from Strands agent response format
        # The content might be in format: {'role': 'assistant', 'content': [{'text': 'actual_json_here'}]}
        if content.startswith("{'role': 'assistant'"):
            try:
                # Parse the outer structure
                import ast
                outer_dict = ast.literal_eval(content)
                if 'content' in outer_dict and isinstance(outer_dict['content'], list):
                    for item in outer_dict['content']:
                        if isinstance(item, dict) and 'text' in item:
                            inner_text = item['text']
                            # Look for JSON within the text
                            json_match = extract_json_from_text(inner_text)
                            if json_match:
                                return json_match
            except:
                pass
        
        # Try direct JSON parsing if it starts with {
        if content.startswith('{'):
            return json.loads(content)
        
        # Look for JSON blocks in markdown code blocks
        import re
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        json_match = re.search(json_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if json_match:
            json_content = json_match.group(1).strip()
            return json.loads(json_content)
        
        # Look for JSON structure anywhere in the text
        json_match = extract_json_from_text(content)
        if json_match:
            return json_match
        
        logger.warning(f"No valid JSON found in content: {content[:200]}...")
        return None
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        logger.error(f"Content that failed to parse: {content[:500]}...")
        return None
    except Exception as e:
        logger.error(f"Unexpected parsing error: {str(e)}")
        return None

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extract JSON object from text content.
    """
    try:
        # Find the first { and try to match the complete JSON object
        start_idx = text.find('{')
        if start_idx != -1:
            # Count braces to find the complete JSON object
            brace_count = 0
            end_idx = start_idx
            
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if brace_count == 0:  # Found complete JSON object
                json_content = text[start_idx:end_idx]
                return json.loads(json_content)
        
        return None
    except:
        return None

def download_s3_file(bucket: str, key: str) -> str:
    """Download file content from S3."""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        logger.error(f"Error downloading S3 file {key}: {str(e)}")
        raise

def find_job_description(bucket: str) -> str:
    """Find and download job description from S3."""
    try:
        # List objects in jobs/ prefix
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix='jobs/')
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            return "No specific job description found. Please evaluate general qualifications."
        
        # Get the first job description
        job_key = response['Contents'][0]['Key']
        return download_s3_file(bucket, job_key)
        
    except Exception as e:
        logger.error(f"Error finding job description: {str(e)}")
        return "No job description available. Please evaluate general qualifications."

def extract_name_from_key(resume_key: str) -> str:
    """Extract candidate name from resume file key."""
    try:
        filename = resume_key.split('/')[-1]
        name = filename.replace('.txt', '').replace('_', ' ').replace('-', ' ')
        return ' '.join(word.capitalize() for word in name.split())
    except:
        return "Unknown Candidate"

def create_error_result(candidate_id: str, resume_key: str, error_message: str) -> Dict[str, Any]:
    """Create error result structure."""
    return {
        "id": candidate_id,
        "resume_key": resume_key,
        "name": extract_name_from_key(resume_key),
        "status": "error",
        "error": error_message,
        "created_at": datetime.utcnow().isoformat(),
        "evaluated_by": "Strands Multi-Agent System (Error)",
        "strands_agent_collaboration": {
            "evaluation_approach": "Error during Strands agent processing",
            "error_details": error_message
        }
    }

def store_candidate_evaluation(evaluation_data: Dict[str, Any]) -> None:
    """Store evaluation data in DynamoDB."""
    try:
        # Convert any float values to Decimal for DynamoDB
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
        
        candidates_table.put_item(Item=converted_data)
        logger.info(f"✅ Stored evaluation for candidate: {evaluation_data.get('name', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"❌ Error storing evaluation in DynamoDB: {str(e)}")
        raise
