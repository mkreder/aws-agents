import boto3
import json
import os
import uuid
from datetime import datetime

def lambda_handler(event, context):
    """
    Lambda function that handles actions for the Bedrock agent.
    Provides data storage and retrieval capabilities for candidate evaluations.
    """
    
    # Extract the action from the event
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', '')
    parameters = event.get('parameters', [])
    request_body = event.get('requestBody', {})
    
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    candidates_table = dynamodb.Table(os.environ['CANDIDATES_TABLE'])
    
    try:
        # Handle the save_evaluation action
        if api_path == '/save_evaluation' and http_method == 'POST':
            return handle_save_evaluation(candidates_table, request_body, action_group, api_path, http_method)
        # Legacy actions
        elif api_path == '/save-candidate' and http_method == 'POST':
            return save_candidate_data(candidates_table, request_body)
        elif api_path == '/get-candidate' and http_method == 'GET':
            return get_candidate_data(candidates_table, parameters)
        else:
            return create_error_response(action_group, api_path, http_method, 400, 
                                       f'Unsupported action: {api_path} {http_method}')
    
    except Exception as e:
        return create_error_response(action_group, api_path, http_method, 500, 
                                   f'Internal server error: {str(e)}')

def handle_save_evaluation(table, request_body, action_group, api_path, http_method):
    """
    Handle the save_evaluation action from the SupervisorAgent.
    """
    # Parse the request body
    data = parse_request_body(request_body)
    
    # Extract required fields
    candidate_id = data.get('candidate_id')
    candidate_name = data.get('candidate_name')
    evaluation_summary = data.get('evaluation_summary')
    rating = data.get('rating')
    resume_key = data.get('resume_key')
    
    if not candidate_id or not candidate_name or not evaluation_summary:
        return create_error_response(action_group, api_path, http_method, 400,
                                   'Missing required fields: candidate_id, candidate_name, evaluation_summary')
    
    # Create the candidate record
    item = {
        'id': candidate_id,
        'name': candidate_name,
        'evaluation_summary': evaluation_summary,
        'status': 'evaluated',
        'timestamp': datetime.utcnow().isoformat(),
        'evaluated_by': 'supervisor-agent'
    }
    
    # Add optional fields if provided
    if rating is not None:
        item['rating'] = rating
    if resume_key:
        item['resume_key'] = resume_key
    
    # Save to DynamoDB
    table.put_item(Item=item)
    
    return create_success_response(action_group, api_path, http_method, {
        'message': f'Evaluation saved successfully for candidate {candidate_name}',
        'candidate_id': candidate_id
    })

def save_candidate_data(table, request_body):
    """Save candidate evaluation data to DynamoDB"""
    
    # Parse the request body
    data = parse_request_body(request_body)
    
    # Generate candidate ID if not provided
    candidate_id = data.get('candidateId', str(uuid.uuid4()))
    
    # Prepare the item to save
    item = {
        'id': candidate_id,
        'name': data.get('name', ''),
        'email': data.get('email', ''),
        'rating': int(data.get('rating', 0)) if data.get('rating') else 0,
        'evaluation': data.get('evaluation', ''),
        'resumeS3Key': data.get('resumeS3Key', ''),
        'createdAt': datetime.utcnow().isoformat(),
        'updatedAt': datetime.utcnow().isoformat()
    }
    
    # Save to DynamoDB
    table.put_item(Item=item)
    
    return create_success_response('CandidateDataActions', '/save-candidate', 'POST', {
        'success': True,
        'message': f'Candidate data saved successfully with ID: {candidate_id}',
        'candidateId': candidate_id
    })

def get_candidate_data(table, parameters):
    """Retrieve candidate data from DynamoDB"""
    
    # Extract candidate ID from parameters
    candidate_id = None
    for param in parameters:
        if param.get('name') == 'candidateId':
            candidate_id = param.get('value')
            break
    
    if not candidate_id:
        return create_error_response('CandidateDataActions', '/get-candidate', 'GET', 400,
                                   'candidateId parameter is required')
    
    # Retrieve from DynamoDB
    response = table.get_item(Key={'id': candidate_id})
    
    if 'Item' not in response:
        return create_error_response('CandidateDataActions', '/get-candidate', 'GET', 404,
                                   f'Candidate with ID {candidate_id} not found')
    
    item = response['Item']
    
    return create_success_response('CandidateDataActions', '/get-candidate', 'GET', {
        'candidateId': item.get('id'),
        'name': item.get('name'),
        'email': item.get('email'),
        'rating': item.get('rating'),
        'evaluation': item.get('evaluation'),
        'resumeS3Key': item.get('resumeS3Key'),
        'createdAt': item.get('createdAt')
    })

def parse_request_body(request_body):
    """Parse request body from various formats"""
    data = {}
    
    if isinstance(request_body, dict):
        if 'content' in request_body:
            content = request_body['content']
            if isinstance(content, dict) and 'application/json' in content:
                json_content = content['application/json']
                if 'properties' in json_content:
                    # Convert properties array to dictionary
                    for prop in json_content['properties']:
                        if 'name' in prop and 'value' in prop:
                            data[prop['name']] = prop['value']
                else:
                    data = json_content
            elif isinstance(content, str):
                data = json.loads(content)
            else:
                data = content
        else:
            data = request_body
    else:
        data = json.loads(request_body) if isinstance(request_body, str) else request_body
    
    return data

def create_success_response(action_group, api_path, http_method, body):
    """Create a successful response"""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpMethod': http_method,
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(body)
                }
            }
        }
    }

def create_error_response(action_group, api_path, http_method, status_code, error_message):
    """Create an error response"""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpMethod': http_method,
            'httpStatusCode': status_code,
            'responseBody': {
                'application/json': {
                    'body': json.dumps({
                        'error': error_message
                    })
                }
            }
        }
    }
