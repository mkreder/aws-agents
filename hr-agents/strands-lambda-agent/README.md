# Strands Multi-Agent HR Resume Evaluation System

This implementation demonstrates a third approach to building AI-powered HR resume evaluation systems using **Strands Agents SDK**. This approach leverages Strands' multi-agent collaboration capabilities with specialized agents working together through natural language communication to provide comprehensive, structured resume evaluations.

## 🏗️ Architecture Overview

The Strands implementation uses a **collaborative multi-agent system** where specialized agents work together to provide comprehensive resume evaluations. Unlike the Step Functions orchestrated approach or Bedrock's supervisor-collaborator pattern, Strands agents communicate naturally and can dynamically adapt their collaboration based on the specific evaluation needs.

**Key Features:**
- **15-Minute Lambda Timeout** - Extended processing time for comprehensive evaluations
- **Structured JSON Output** - Consistent data format matching bedrock-agent implementation
- **Proper Layer Configuration** - Fixed Lambda layer structure for reliable deployments
- **S3 Versioning Disabled** - Clean stack deletion for development workflows

```
S3 Upload → Lambda Trigger → Strands Agent Swarm
                                      ↓
┌─────────────────────────────────────────────────────────┐
│  Strands Multi-Agent Collaboration                     │
│                                                         │
│  ┌─────────────────┐    ┌─────────────────┐           │
│  │ HR Coordinator  │ ←→ │ Resume Parser   │           │
│  │ Agent           │    │ Agent           │           │
│  │                 │    └─────────────────┘           │
│  │ Orchestrates &  │           ↕                      │
│  │ Synthesizes     │    ┌─────────────────┐           │
│  │ Final Report    │ ←→ │ Job Analyzer    │           │
│  │                 │    │ Agent           │           │
│  │                 │    └─────────────────┘           │
│  │                 │           ↕                      │
│  │                 │    ┌─────────────────┐           │
│  │                 │ ←→ │ Skills Evaluator│           │
│  │                 │    │ Agent           │           │
│  │                 │    └─────────────────┘           │
│  │                 │           ↕                      │
│  │                 │    ┌─────────────────┐           │
│  │                 │ ←→ │ Interview Prep  │           │
│  │                 │    │ Agent           │           │
│  └─────────────────┘    └─────────────────┘           │
└─────────────────────────────────────────────────────────┘
                              ↓
                         DynamoDB Storage
```

## 🚀 Key Features

### Strands-Specific Advantages

- **Natural Agent Communication**: Agents communicate in natural language, enabling flexible collaboration patterns
- **Dynamic Tool Usage**: Agents can dynamically load and use tools based on evaluation needs
- **Adaptive Workflows**: The system can adapt evaluation processes based on candidate profiles
- **Rich Context Sharing**: Agents maintain shared context throughout the evaluation process
- **Extensible Architecture**: Easy to add new specialized agents or modify existing ones

### Core Capabilities

- **Automated Resume Processing** - Upload resumes to S3 for automatic evaluation
- **Multi-Agent Collaboration** - Specialized agents work together naturally
- **Comprehensive Analysis** - Skills, experience, education, and cultural fit assessment
- **Gap Identification** - Identifies missing skills and experience gaps
- **Candidate Rating** - Numerical scoring with detailed justification
- **Interview Preparation** - Generates structured interview questions
- **Structured Data Storage** - Results stored in DynamoDB with consistent schema

## 🛠️ Technology Stack

### Core Services
- **Strands Agents SDK** - Multi-agent collaboration framework (v0.1.9)
- **Amazon Bedrock** - Claude 3.5 Sonnet v2 for enhanced AI processing
- **AWS Lambda** - Serverless compute with 15-minute timeout for comprehensive processing
- **Amazon S3** - Document storage and event triggers (versioning disabled)
- **Amazon DynamoDB** - NoSQL database for evaluation results
- **AWS IAM** - Identity and access management

### Strands Components
- **Agent Swarm** - Coordinated multi-agent collaboration
- **Custom Tools** - Specialized tools for HR evaluation tasks
- **Lambda Layer** - Properly configured dependencies layer for Strands SDK
- **Structured JSON Parsing** - Consistent output format across implementations

## 📁 Project Structure

```
strands-agent/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── template-infrastructure.yaml # Infrastructure resources (S3, DynamoDB)
├── template-lambda.yaml        # Lambda functions and layer template
├── deploy.sh                   # Automated deployment script
├── create_lambda_package.py    # Lambda packaging with proper layer structure
├── Dockerfile.deps             # Docker configuration for Linux dependencies
├── functions/                  # Lambda function code
│   └── resume_processor/       # Main processing function
│       ├── app.py             # Main Lambda handler with structured JSON prompts
│       └── requirements.txt   # Function-specific dependencies
└── packaging/                  # Build artifacts (created during deployment)
    ├── dependencies.zip       # Lambda layer with Strands SDK
    ├── app.zip               # Lambda function code
    └── _dependencies/        # Extracted dependencies
```

## 🤖 Agent Implementation

The Strands implementation uses a **single Lambda function** with **embedded multi-agent logic** rather than separate agent files. All agents are implemented as specialized prompts within the main Lambda function, ensuring consistent structured JSON output.

### Supervisor Agent (HR Coordinator)
**Role**: Orchestrates the entire evaluation process and coordinates with specialized agents
**Implementation**: Main coordinator that manages the multi-agent workflow
**Output**: Comprehensive structured JSON evaluation

### Specialized Agents (Implemented as Structured Prompts)
All specialized agents use identical prompts to the Bedrock and StepFunctions agent implementations to ensure consistent data quality:

1. **Resume Parser Agent** - Extracts structured information (personal info, experience, education, skills)
2. **Job Analyzer Agent** - Analyzes job requirements with required/preferred skills categorization  
3. **Resume Evaluator Agent** - Evaluates candidate fit with quantified skills matching
4. **Gap Identifier Agent** - Identifies specific missing skills and concerns
5. **Candidate Rater Agent** - Provides numerical rating (1-5) with detailed justification
6. **Interview Notes Agent** - Generates specific questions and focus areas

### Key Implementation Features
- **Structured JSON Prompts**: Each agent outputs JSON with specific categories
- **Bedrock-Compatible Format**: Identical data structure to the other implementations
- **Error Handling**: Robust parsing with fallback structures
- **15-Minute Timeout**: Extended processing time for comprehensive evaluations

## 🔧 Custom Tools

### Resume Processing Tools
```python
@tool
def extract_resume_sections(resume_text: str) -> dict:
    """Extract structured sections from resume text"""
    # Implementation for parsing resume sections

@tool
def identify_skills(text: str) -> list:
    """Identify technical and soft skills from text"""
    # Implementation for skill identification
```

### Job Analysis Tools
```python
@tool
def parse_job_requirements(job_description: str) -> dict:
    """Parse job requirements into structured format"""
    # Implementation for job requirement parsing

@tool
def categorize_requirements(requirements: list) -> dict:
    """Categorize requirements by type and priority"""
    # Implementation for requirement categorization
```

### Evaluation Tools
```python
@tool
def calculate_skill_match(candidate_skills: list, required_skills: list) -> float:
    """Calculate percentage match between candidate and required skills"""
    # Implementation for skill matching algorithm

@tool
def generate_rating(evaluation_data: dict) -> dict:
    """Generate numerical rating with justification"""
    # Implementation for candidate rating
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- AWS SAM CLI installed
- Python 3.11 or later
- Docker (for building Linux dependencies)
- Access to Amazon Bedrock Claude 3.5 Sonnet v2 model

### Deployment

1. **Navigate to the Strands implementation**:
   ```bash
   cd strands-agent
   ```

2. **Deploy the complete system**:
   ```bash
   ./deploy.sh
   ```

   The deployment script will:
   - Deploy infrastructure (S3 bucket, DynamoDB table)
   - Build Linux dependencies using Docker
   - Create Lambda deployment packages
   - Deploy Lambda function with proper layer configuration
   - Configure S3 event triggers

3. **Upload sample data for testing**:
   ```bash
   # Upload job description
   aws s3 cp ../samples/jobs/ai_engineer_position.txt s3://strands-agent-documents-dev/jobs/
   
   # Upload resume (triggers processing)
   aws s3 cp ../samples/resumes/john_doe_ai_engineer.txt s3://strands-agent-documents-dev/resumes/
   ```

4. **Monitor processing**:
   ```bash
   # View logs
   aws logs tail /aws/lambda/strands-agent-resume-processor-dev --region us-east-1 --follow
   
   # Check results
   aws dynamodb scan --table-name strands-agent-candidates-dev --region us-east-1
   ```

## 📋 Evaluation Output Structure

The Strands implementation produces comprehensive evaluation data consistent with the other implementations:

```json
{
  "id": "candidate-uuid",
  "name": "Candidate Name",
  "resume_key": "resumes/candidate_resume.txt",
  "status": "completed",
  "job_title": "Senior AI Engineer",
  "evaluated_by": "strands-multi-agent",
  "evaluation_results": {
    "agent_collaboration_summary": {
      "coordinator": "HR Coordinator Agent",
      "collaborators": [
        "Resume Parser Agent",
        "Job Analyzer Agent", 
        "Skills Evaluator Agent",
        "Interview Prep Agent"
      ],
      "evaluation_approach": "Multi-agent collaborative analysis"
    },
    "skills_summary": {
      "programming_languages": ["Python", "SQL", "Java"],
      "ml_frameworks": ["TensorFlow", "PyTorch", "Scikit-learn"],
      "cloud_platforms": ["AWS", "GCP"],
      "tools": ["Docker", "Git", "Kubernetes"],
      "skill_match_percentage": 85.5
    },
    "experience_analysis": {
      "years_of_experience": "5+",
      "relevant_roles": ["ML Engineer", "Data Scientist"],
      "key_projects": ["Recommendation System", "NLP Pipeline"],
      "experience_relevance": "High"
    },
    "job_match_analysis": {
      "overall_fit": "Excellent",
      "technical_alignment": "Strong",
      "experience_match": "Very Good",
      "cultural_fit_indicators": "Positive"
    }
  },
  "candidate_rating": {
    "rating": 4.2,
    "reasoning": "Strong technical background with relevant experience. Minor gaps in specific technologies but demonstrates learning ability.",
    "strengths": [
      "Extensive ML/AI experience",
      "Strong programming skills",
      "Relevant project experience"
    ],
    "areas_for_development": [
      "MLOps experience could be stronger",
      "Limited large-scale system experience"
    ]
  },
  "interview_notes": {
    "technical_questions": [
      "Describe your experience with production ML systems",
      "How do you approach model versioning and deployment?"
    ],
    "behavioral_questions": [
      "Tell me about a challenging ML project you led",
      "How do you stay current with ML/AI developments?"
    ],
    "areas_to_explore": [
      "MLOps practices and experience",
      "Team collaboration and leadership",
      "Approach to model monitoring and maintenance"
    ]
  }
}
```

## 🔍 Monitoring & Debugging

### Strands-Specific Monitoring
- **Agent Coordination Logs**: Detailed logs of multi-agent collaboration
- **Structured JSON Parsing**: Monitor JSON extraction and validation
- **Layer Attachment**: Verify proper Strands SDK loading
- **Processing Time**: Track 15-minute evaluation workflows

### AWS Service Monitoring
- **CloudWatch Logs**: Lambda function execution with detailed agent interactions
- **DynamoDB Metrics**: Database performance and structured data storage
- **S3 Event Tracking**: Document upload and processing events
- **Lambda Metrics**: Function duration, memory usage, and error rates

### Debug Commands
```bash
# Monitor real-time logs
aws logs tail /aws/lambda/strands-agent-resume-processor-dev --region us-east-1 --follow

# Check layer attachment
aws lambda get-function --function-name strands-agent-resume-processor-dev --region us-east-1 | jq '.Configuration.Layers'

# View evaluation results
aws dynamodb scan --table-name strands-agent-candidates-dev --region us-east-1 | jq '.Items[0]'

# Check S3 bucket contents
aws s3 ls s3://strands-agent-documents-dev/ --recursive
```

## 🆚 Comparison with Other Implementations

| Aspect | Step Functions | Bedrock Agents | Strands Agents |
|--------|----------------|----------------|----------------|
| **Architecture** | Orchestrated pipeline | Supervisor-collaborator | Embedded multi-agent |
| **Agent Communication** | State passing | Structured messages | Natural language coordination |
| **Flexibility** | Structured workflow | Guided collaboration | Adaptive collaboration |
| **Processing Time** | Fast (< 1 min) | Medium (2-5 min) | Comprehensive (5-15 min) |
| **Development Model** | Infrastructure-first | AI-first | Agent-first |
| **Customization** | Code modifications | Instruction updates | Prompt specialization |
| **Scalability** | Excellent | Good | Excellent |
| **Debugging** | Step-by-step | Agent traces | Agent coordination logs |
| **Data Consistency** | Good | Excellent | Excellent (bedrock-compatible) |

## 🔧 Configuration

### Environment Variables
```bash
# AWS Configuration
AWS_REGION=us-east-1
CANDIDATES_TABLE=strands-agent-candidates-dev
DOCUMENTS_BUCKET=strands-agent-documents-dev

# Strands Configuration
STRANDS_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
STRANDS_DEBUG_LEVEL=INFO

# Lambda Configuration
LAMBDA_TIMEOUT=900  # 15 minutes
LAMBDA_MEMORY=1024  # MB
```

### Model Configuration
The implementation uses Claude 3.7 Sonnet for consistent performance:
```python
MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
```

### Deployment Configuration
```bash
# Infrastructure Stack
INFRASTRUCTURE_STACK=strands-agent-infrastructure

# Lambda Stack  
LAMBDA_STACK=strands-agent-lambda

# Environment
ENVIRONMENT=dev
```

## 🚀 Advanced Features

### Dynamic Agent Loading
```python
from strands_tools import load_tool

@tool
def load_specialist_agent(specialty: str) -> Agent:
    """Dynamically load specialist agents based on evaluation needs"""
    # Implementation for dynamic agent loading
```

### MCP Integration
```python
from strands.tools.mcp import MCPClient

# Connect to AWS Documentation MCP server
aws_docs_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

# Add MCP tools to agents
with aws_docs_client:
    tools = aws_docs_client.list_tools_sync()
    agent = Agent(tools=tools)
```

### Workflow Orchestration
```python
from strands_tools import workflow

@tool
def evaluation_workflow(candidate_data: dict) -> dict:
    """Orchestrate the complete evaluation workflow"""
    # Implementation for workflow orchestration
```

## 💰 Cost Optimization

### Strands-Specific Optimizations
- **Agent Specialization**: Use focused agents to reduce token usage
- **Tool Efficiency**: Optimize custom tools for minimal API calls
- **Context Management**: Efficient context sharing between agents
- **Batch Processing**: Process multiple candidates in parallel

### AWS Service Optimizations
- **Lambda Memory Tuning**: Optimize memory allocation for agent workloads
- **DynamoDB Capacity**: Use on-demand billing for variable workloads
- **S3 Lifecycle Policies**: Manage document storage costs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch for your agent or tool
3. Implement your changes with appropriate tests
4. Update documentation and examples
5. Submit a pull request with detailed description

## 📄 License

This project is licensed under the MIT License

