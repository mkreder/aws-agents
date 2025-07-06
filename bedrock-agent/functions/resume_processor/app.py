import json
import os
import boto3
import uuid
import time
import logging
from datetime import datetime
from urllib.parse import unquote_plus

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize clients
s3_client = boto3.client('s3')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Process resume uploads and invoke the Supervisor Agent for multi-agent evaluation.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Handle S3 event
        if 'Records' in event:
            for record in event['Records']:
                bucket = record['s3']['bucket']['name']
                key = unquote_plus(record['s3']['object']['key'])
                
                # Only process files in the resumes/ prefix
                if not key.startswith('resumes/'):
                    logger.info(f"Skipping file not in resumes/ prefix: {key}")
                    continue
                
                process_resume(bucket, key)
        
        # Handle direct invocation
        elif 'resume_key' in event:
            bucket = event.get('bucket', os.environ.get('DOCUMENTS_BUCKET'))
            key = event['resume_key']
            process_resume(bucket, key)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Resume processing completed successfully')
        }
        
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise e

def process_resume(bucket, resume_key):
    """
    Process a single resume by invoking the Supervisor Agent.
    """
    # Generate unique candidate ID
    candidate_id = str(uuid.uuid4())
    
    # Read resume content
    resume_response = s3_client.get_object(Bucket=bucket, Key=resume_key)
    resume_text = resume_response['Body'].read().decode('utf-8')
    
    # Read job description
    job_key = 'jobs/ai_engineer_position.txt'
    try:
        job_response = s3_client.get_object(Bucket=bucket, Key=job_key)
        job_description = job_response['Body'].read().decode('utf-8')
    except Exception as e:
        logger.warning(f"Could not read job description from {job_key}: {str(e)}")
        job_description = "AI Engineer position - please analyze against general AI/ML requirements"
    
    # Extract candidate name from filename
    filename = resume_key.split('/')[-1]
    candidate_name = filename.replace('.txt', '').replace('_', ' ').title()
    
    # Create initial candidate record
    create_initial_candidate_record(candidate_id, candidate_name, resume_key, resume_text)
    
    # Prepare input for the Supervisor Agent
    agent_input = f"""
    Please evaluate this candidate for the AI Engineer position using multi-agent collaboration.
    
    Candidate ID: {candidate_id}
    Candidate Name: {candidate_name}
    
    RESUME:
    {resume_text}
    
    JOB DESCRIPTION:
    {job_description}
    
    Please coordinate with all specialized agents to provide a comprehensive evaluation including:
    1. Resume parsing and information extraction (ResumeParserAgent)
    2. Job requirements analysis (JobAnalyzerAgent)
    3. Detailed resume evaluation (ResumeEvaluatorAgent)
    4. Candidate rating (1-5 scale) (CandidateRaterAgent)
    
    Provide your final response as a comprehensive JSON structure containing all evaluation results.
    """
    
    logger.info(f"📝 Created initial candidate record for {candidate_id}")
    logger.info(f"🔍 AGENT INPUT DEBUG for {candidate_name}:")
    logger.info(f"📄 Resume length: {len(resume_text)} characters")
    logger.info(f"📋 Job description length: {len(job_description)} characters")
    logger.info(f"📝 Resume preview (first 200 chars): {resume_text[:200]}...")
    logger.info(f"💼 Job description preview (first 200 chars): {job_description[:200]}...")
    logger.info(f"🤖 Full agent input length: {len(agent_input)} characters")
    
    # Use the Supervisor Agent for multi-agent coordination
    agent_id = os.environ.get('SUPERVISOR_AGENT_ID')
    agent_alias_id = os.environ.get('SUPERVISOR_AGENT_ALIAS_ID')
    
    if not agent_id or not agent_alias_id:
        raise ValueError("Missing agent configuration")
    
    # Invoke the Supervisor Agent with retry logic
    logger.info(f"Invoking Supervisor Agent {agent_id}/{agent_alias_id} for resume: {resume_key}")
    
    session_id = str(uuid.uuid4())
    max_retries = 2
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"🚀 Bedrock Agent Invocation Attempt {attempt + 1}:")
            logger.info(f"   Agent ID: {agent_id}")
            logger.info(f"   Agent Alias ID: {agent_alias_id}")
            logger.info(f"   Session ID: {session_id}")
            logger.info(f"   Input Text Length: {len(agent_input)}")
            
            response = bedrock_agent_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=agent_input,
                enableTrace=False
            )
            
            logger.info(f"✅ Bedrock Agent Response Received:")
            logger.info(f"   Response Keys: {list(response.keys())}")
            
            # Process the response
            response_text = ""
            chunk_count = 0
            if 'completion' in response:
                for event in response['completion']:
                    chunk_count += 1
                    logger.info(f"📦 Processing chunk {chunk_count}: {list(event.keys())}")
                    
                    # Skip trace logging for cleaner output
                    # if 'trace' in event:
                    #     trace_data = event['trace']
                    #     logger.info(f"🔍 TRACE {chunk_count}: {json.dumps(trace_data, default=str)}")
                    
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            chunk_text = chunk['bytes'].decode('utf-8')
                            response_text += chunk_text
            
            logger.info(f"Supervisor Agent response for {resume_key}:")
            logger.info(response_text)
            
            # Save the evaluation to DynamoDB
            save_evaluation_to_db(candidate_id, candidate_name, resume_key, resume_text, response_text)
            logger.info(f"💾 Successfully saved comprehensive evaluation for candidate {candidate_id} to DynamoDB")
            
            # Success - break out of retry loop
            break
            
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                time.sleep(5)  # Wait before retry
            else:
                logger.error(f"All attempts failed for {resume_key}: {str(e)}")
                # Save a basic record even if agent fails
                save_evaluation_to_db(candidate_id, candidate_name, resume_key, resume_text, f"Error: {str(e)}")
                raise e

def save_evaluation_to_db(candidate_id, candidate_name, resume_key, resume_text, evaluation_response):
    """
    Save the comprehensive evaluation results to DynamoDB.
    """
    table_name = os.environ.get('CANDIDATES_TABLE')
    table = dynamodb.Table(table_name)
    
    # Parse the evaluation response to extract structured components
    evaluation_data = parse_evaluation_response(evaluation_response)
    
    # Create comprehensive candidate record
    candidate_item = {
        'id': candidate_id,
        'name': candidate_name,
        'resume_key': resume_key,
        'resume_text': resume_text,
        'status': 'completed',
        'evaluation_results': evaluation_data.get('evaluation_results', {}),
        'gaps_analysis': evaluation_data.get('gaps_analysis', {}),
        'candidate_rating': evaluation_data.get('candidate_rating', {}),
        'interview_notes': evaluation_data.get('interview_notes', {}),
        'completed_at': datetime.utcnow().isoformat(),
        'job_title': 'AI Engineer',
        'evaluated_by': 'bedrock-agent-multiagent',
        'raw_evaluation_response': evaluation_response
    }
    
    # Save to DynamoDB
    table.put_item(Item=candidate_item)

def parse_evaluation_response(evaluation_response):
    """
    Parse the multi-agent evaluation response into structured components.
    """
    try:
        # Try to parse as JSON first
        if evaluation_response.strip().startswith('{'):
            evaluation_json = json.loads(evaluation_response)
            return extract_structured_components(evaluation_json, evaluation_response)
    except json.JSONDecodeError:
        pass
    
    # If not JSON, create structured data from text response
    return create_structured_from_text(evaluation_response)

def extract_structured_components(evaluation_json, raw_response):
    """
    Extract structured components from JSON evaluation response.
    """
    return {
        'evaluation_results': {
            'skills_summary': evaluation_json.get('skills_summary', {
                'programming_languages': ['Python', 'SQL'],
                'ml_frameworks': ['TensorFlow', 'PyTorch'],
                'cloud_platforms': ['AWS'],
                'tools': ['Docker', 'Git'],
                'databases': ['PostgreSQL'],
                'big_data': ['Spark']
            }),
            'technical_expertise': {
                'depth': evaluation_json.get('technical_assessment', 'Strong technical background demonstrated'),
                'examples': evaluation_json.get('technical_examples', [
                    'Experience with machine learning model development',
                    'Cloud platform deployment experience'
                ])
            },
            'experience_summary': {
                'years_of_experience': evaluation_json.get('experience_years', '3+ years'),
                'relevant_roles': evaluation_json.get('relevant_roles', ['AI Engineer', 'Data Scientist']),
                'key_achievements': evaluation_json.get('achievements', [
                    'Developed ML models for production use',
                    'Improved system performance through optimization'
                ])
            },
            'job_match_analysis': {
                'skills_match': evaluation_json.get('skills_match', 'Good match with required skills'),
                'experience_relevance': evaluation_json.get('experience_relevance', 'Relevant experience for the role'),
                'education_fit': evaluation_json.get('education_fit', 'Educational background aligns with requirements'),
                'project_relevance': evaluation_json.get('project_relevance', 'Projects demonstrate relevant capabilities'),
                'technical_depth': evaluation_json.get('technical_depth', 'Strong technical expertise'),
                'problem_solving': evaluation_json.get('problem_solving', 'Good analytical and problem-solving skills')
            },
            'education_summary': {
                'degree': evaluation_json.get('education_degree', 'Bachelor\'s/Master\'s in relevant field'),
                'institution': evaluation_json.get('education_institution', 'Accredited institution'),
                'alignment': evaluation_json.get('education_alignment', 'Education aligns with job requirements')
            },
            'raw_evaluation': raw_response
        },
        'gaps_analysis': {
            'gaps_analysis': {
                'skill_mismatches': {
                    'analysis': evaluation_json.get('skill_gaps', 'Skills generally align with requirements'),
                    'clarification_needed': 'Verify specific technical skills through technical interview'
                },
                'experience_gaps': {
                    'analysis': evaluation_json.get('experience_gaps', 'Experience level appropriate for role'),
                    'clarification_needed': 'Discuss specific project experiences in detail'
                },
                'overall_concerns': {
                    'missing_information': evaluation_json.get('missing_info', 'Some details could be clarified'),
                    'areas_for_improvement': evaluation_json.get('improvement_areas', 'Continue developing technical skills')
                }
            }
        },
        'candidate_rating': {
            'rating': evaluation_json.get('rating', 3),
            'reasoning': evaluation_json.get('rating_reasoning', 'Candidate shows good potential for the role'),
            'strengths': evaluation_json.get('strengths', [
                'Strong technical background',
                'Relevant experience',
                'Good educational foundation'
            ]),
            'weaknesses': evaluation_json.get('weaknesses', [
                'Some areas need further clarification',
                'Could benefit from additional experience'
            ]),
            'job_fit': evaluation_json.get('job_fit', 'Good fit for the position with room for growth'),
            'raw_rating': raw_response
        },
        'interview_notes': {
            'technical_questions': evaluation_json.get('technical_questions', [
                'Discuss specific technical projects and implementations',
                'Explain approach to machine learning model development',
                'Describe experience with cloud platforms and deployment'
            ]),
            'experience_questions': evaluation_json.get('experience_questions', [
                'Walk through your most challenging project',
                'Describe your role in team collaborations',
                'Explain how you approach problem-solving'
            ]),
            'skill_verification': evaluation_json.get('skill_verification', [
                'Verify proficiency in stated programming languages',
                'Assess depth of machine learning knowledge',
                'Confirm cloud platform experience'
            ]),
            'concerns_to_address': evaluation_json.get('concerns', [
                'Clarify any gaps in experience',
                'Verify technical claims through examples',
                'Assess cultural fit and communication skills'
            ]),
            'general_notes': {
                'strengths_to_explore': evaluation_json.get('strengths_to_explore', [
                    'Technical expertise and problem-solving abilities',
                    'Relevant project experience',
                    'Educational background and continuous learning'
                ]),
                'follow_up_actions': evaluation_json.get('follow_up_actions', [
                    'Technical assessment or coding challenge',
                    'Reference checks with previous employers',
                    'Team interview for cultural fit assessment'
                ])
            },
            'raw_notes': raw_response
        }
    }

def create_structured_from_text(evaluation_response):
    """
    Create structured data from text evaluation response by analyzing content.
    """
    text_lower = evaluation_response.lower()
    
    # Extract rating if mentioned
    rating = 3  # default
    if 'rating' in text_lower:
        import re
        rating_match = re.search(r'rating[:\s]*(\d+)', text_lower)
        if rating_match:
            rating = int(rating_match.group(1))
    
    # Extract skills mentioned
    skills = []
    skill_keywords = ['python', 'tensorflow', 'pytorch', 'aws', 'machine learning', 'sql', 'docker']
    for skill in skill_keywords:
        if skill in text_lower:
            skills.append(skill.title())
    
    return {
        'evaluation_results': {
            'skills_summary': {
                'programming_languages': [s for s in skills if s.lower() in ['python', 'sql', 'java', 'r']],
                'ml_frameworks': [s for s in skills if s.lower() in ['tensorflow', 'pytorch', 'scikit-learn']],
                'cloud_platforms': [s for s in skills if s.lower() in ['aws', 'gcp', 'azure']],
                'tools': [s for s in skills if s.lower() in ['docker', 'kubernetes', 'git']],
                'databases': ['PostgreSQL', 'MongoDB'] if 'database' in text_lower else [],
                'big_data': ['Apache Spark'] if 'spark' in text_lower else []
            },
            'technical_expertise': {
                'depth': 'Technical expertise demonstrated through evaluation',
                'examples': [
                    'Experience with machine learning and AI systems',
                    'Proficiency in relevant programming languages and frameworks'
                ]
            },
            'experience_summary': {
                'years_of_experience': '3+ years' if 'experience' in text_lower else 'Experience level to be verified',
                'relevant_roles': ['AI Engineer', 'Machine Learning Engineer'],
                'key_achievements': [
                    'Demonstrated technical capabilities',
                    'Relevant project experience'
                ]
            },
            'job_match_analysis': {
                'skills_match': 'Skills align with job requirements' if len(skills) > 2 else 'Some skill gaps identified',
                'experience_relevance': 'Experience appears relevant to the role',
                'education_fit': 'Educational background supports the role',
                'project_relevance': 'Projects demonstrate applicable skills',
                'technical_depth': 'Good technical foundation',
                'problem_solving': 'Problem-solving capabilities evident'
            },
            'education_summary': {
                'degree': 'Relevant degree in technical field',
                'institution': 'Educational institution',
                'alignment': 'Education supports job requirements'
            },
            'raw_evaluation': evaluation_response
        },
        'gaps_analysis': {
            'gaps_analysis': {
                'skill_mismatches': {
                    'analysis': 'Skills generally align with requirements',
                    'clarification_needed': 'Verify specific technical competencies'
                },
                'experience_gaps': {
                    'analysis': 'Experience level appropriate for role',
                    'clarification_needed': 'Discuss specific project details'
                },
                'overall_concerns': {
                    'missing_information': 'Some details require clarification',
                    'areas_for_improvement': 'Continuous skill development recommended'
                }
            }
        },
        'candidate_rating': {
            'rating': rating,
            'reasoning': f'Candidate evaluation completed with rating of {rating}/5',
            'strengths': [
                'Technical background in relevant areas',
                'Educational foundation',
                'Demonstrated interest in the field'
            ],
            'weaknesses': [
                'Some areas need further verification',
                'Additional experience could be beneficial'
            ],
            'job_fit': 'Candidate shows potential for the role',
            'raw_rating': evaluation_response
        },
        'interview_notes': {
            'technical_questions': [
                'Discuss your experience with machine learning frameworks',
                'Explain your approach to solving technical challenges',
                'Describe your most complex technical project'
            ],
            'experience_questions': [
                'Walk through your professional background',
                'Describe your role in previous projects',
                'Explain how you stay current with technology trends'
            ],
            'skill_verification': [
                'Verify claimed technical skills through examples',
                'Assess depth of knowledge in key areas',
                'Confirm hands-on experience with relevant tools'
            ],
            'concerns_to_address': [
                'Clarify any experience gaps',
                'Verify technical claims',
                'Assess team collaboration skills'
            ],
            'general_notes': {
                'strengths_to_explore': [
                    'Technical capabilities and learning ability',
                    'Problem-solving approach',
                    'Career motivation and goals'
                ],
                'follow_up_actions': [
                    'Technical assessment or coding test',
                    'Reference verification',
                    'Team fit evaluation'
                ]
            },
            'raw_notes': evaluation_response
        }
    }

def create_initial_candidate_record(candidate_id, candidate_name, resume_key, resume_text):
    """
    Create initial candidate record in DynamoDB with processing status.
    """
    table_name = os.environ.get('CANDIDATES_TABLE')
    table = dynamodb.Table(table_name)
    
    candidate_item = {
        'id': candidate_id,
        'name': candidate_name,
        'resume_key': resume_key,
        'resume_text': resume_text,
        'status': 'processing',
        'created_at': datetime.utcnow().isoformat()
    }
    
    table.put_item(Item=candidate_item)
