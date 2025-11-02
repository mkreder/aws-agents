# Bedrock Agents HR Resume Evaluation System

This implementation demonstrates a multi-agent AI approach to building AI-powered HR resume evaluation systems using **Amazon Bedrock Agents**. This approach leverages Bedrock's native multi-agent collaboration capabilities with a Supervisor Agent coordinating specialized collaborator agents to provide comprehensive, structured resume evaluations.

## 🏗️ Architecture Overview

The Bedrock Agents implementation uses a **supervisor-collaborator pattern** where a Supervisor Agent orchestrates the evaluation process by coordinating with specialized collaborator agents. Each agent has specific expertise and responsibilities, working together through Amazon's managed AI collaboration framework.

**Key Features:**
- **Native AI Agent Collaboration** - Built-in multi-agent coordination by Amazon
- **Supervisor-Collaborator Pattern** - Hierarchical agent organization
- **Managed Agent Communication** - Amazon handles agent-to-agent messaging
- **Advanced AI Reasoning** - Sophisticated decision-making capabilities

```
S3 Upload → Lambda Trigger → Bedrock Agent Invocation
                                      ↓
┌─────────────────────────────────────────────────────────┐
│  Amazon Bedrock Multi-Agent Collaboration              │
│                                                         │
│  ┌─────────────────┐                                   │
│  │ Supervisor      │                                   │
│  │ Agent           │                                   │
│  │                 │                                   │
│  │ Orchestrates &  │ ←→ AgentCommunication__sendMessage│
│  │ Coordinates     │                                   │
│  │ Workflow        │                                   │
│  └─────────────────┘                                   │
│           ↓                                             │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Collaborator Agents                                 │ │
│  │                                                     │ │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │ │
│  │ │Resume Parser│ │Job Analyzer │ │Resume       │   │ │
│  │ │Agent        │ │Agent        │ │Evaluator    │   │ │
│  │ └─────────────┘ └─────────────┘ │Agent        │   │ │
│  │                                 └─────────────┘   │ │
│  │ ┌─────────────┐                                   │ │
│  │ │Candidate    │                                   │ │
│  │ │Rater Agent  │                                   │ │
│  │ └─────────────┘                                   │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              ↓
                         DynamoDB Storage
```

## 🚀 Key Features

### Bedrock Agents-Specific Advantages

- **Native Multi-Agent Framework**: Built-in agent collaboration and communication
- **Managed Complexity**: Amazon handles agent coordination and message routing
- **Advanced AI Reasoning**: Sophisticated agent-to-agent decision making
- **Built-in Memory**: Conversation context maintained across agent interactions
- **Scalable Architecture**: Automatic scaling of agent workloads

### Core Capabilities

- **Automated Resume Processing** - Upload resumes to S3 for automatic evaluation
- **Multi-Agent Collaboration** - Supervisor coordinates with specialized agents
- **Comprehensive Analysis** - Skills, experience, education, and cultural fit assessment
- **Gap Identification** - Identifies missing skills and experience gaps
- **Candidate Rating** - Numerical scoring with detailed justification
- **Interview Preparation** - Generates structured interview questions
- **Structured Data Storage** - Results stored in DynamoDB with consistent schema

## 🛠️ Technology Stack

### Core Services
- **Amazon Bedrock Agents** - Multi-agent AI collaboration framework
- **Amazon Bedrock** - Claude Sonnet 3.7 for enhanced AI processing
- **AWS Lambda** - Serverless compute for agent invocation and processing
- **Amazon S3** - Document storage and event triggers
- **Amazon DynamoDB** - NoSQL database for evaluation results
- **AWS IAM** - Identity and access management

### Bedrock Agents Components
- **Supervisor Agent** - Workflow orchestration and coordination
- **Collaborator Agents** - Specialized agents for specific evaluation tasks
- **Agent Communication** - Built-in messaging between agents
- **Agent Memory** - Conversation context and state management

## 📁 Project Structure

```
bedrock-agent/
├── README.md                      # This file
├── template-agents-phase1.yaml    # Bedrock Agents SAM template
├── template-lambda.yaml           # Lambda functions SAM template
├── deploy.sh                      # Complete deployment script
├── destroy-all.sh                 # Resource cleanup script
├── upload_samples.py              # Sample data upload utility
├── functions/                     # Lambda function source code
│   ├── resume_processor/          # Main processing logic
│   └── agent_executor/            # Agent execution handler
└── samples/                       # Sample data for testing
    ├── jobs/                      # Sample job descriptions
    └── resumes/                   # Sample resumes
```

## 🤖 Multi-Agent System

The Bedrock Agents implementation uses a sophisticated multi-agent architecture:

### Supervisor Agent (HR Evaluation Coordinator)
**Role**: Orchestrates the entire evaluation process and coordinates with collaborator agents
**Responsibilities**: 
- Delegates tasks to specialized collaborator agents
- Compiles comprehensive evaluation reports
- Ensures consistent evaluation quality
- Manages workflow execution

**Communication**: Uses `AgentCommunication__sendMessage` to coordinate with specialists

### Collaborator Agents

#### 1. Resume Parser Agent
**Purpose**: Extracts structured information from resumes
**Specialization**: Personal info, experience, education, skills parsing
**Model**: Claude Sonnet 3.7 for accurate text extraction
**Output**: Structured candidate profile data

#### 2. Job Analyzer Agent
**Purpose**: Analyzes job descriptions and requirements
**Specialization**: Required/preferred skills, experience levels, qualifications
**Model**: Claude Sonnet 3.7 for requirement analysis
**Output**: Structured job requirement profile

#### 3. Resume Evaluator Agent
**Purpose**: Evaluates candidate fit against job requirements
**Specialization**: Skills matching, experience relevance, education alignment
**Model**: Claude Sonnet 3.7 for comprehensive evaluation
**Output**: Detailed fit analysis and recommendations

#### 4. Candidate Rater Agent
**Purpose**: Provides numerical rating with detailed justification
**Specialization**: Objective scoring, strengths/weaknesses analysis
**Model**: Claude Sonnet 3.7 for consistent rating
**Output**: 1-5 rating scale with comprehensive reasoning

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- AWS SAM CLI installed
- Python 3.11 or later
- Access to Amazon Bedrock Agents and Claude Sonnet 3.7 model

### Complete Deployment (Recommended)

Use the comprehensive deployment script that handles multi-agent setup:

```bash
./deploy.sh [profile] [region] [environment]
```

Example:
```bash
./deploy.sh personal us-east-1 dev
```

This script will:
1. Deploy all Bedrock Agents (Supervisor + Collaborators)
2. Configure multi-agent collaboration relationships
3. Deploy Lambda functions for agent invocation
4. Set up S3 event notifications
5. Upload sample data for testing

### Manual Deployment

If you prefer step-by-step deployment:

1. **Deploy Bedrock Agents**:
   ```bash
   sam deploy --template-file template-agents-phase1.yaml --stack-name bedrock-agent-agents
   ```

2. **Configure Agent Collaboration** (see `deploy.sh` for details):
   ```bash
   # Associate collaborators with supervisor
   aws bedrock-agent associate-agent-collaborator \
     --agent-id $SUPERVISOR_ID \
     --agent-version DRAFT \
     --collaborator-agent-id $COLLABORATOR_ID
   ```

3. **Deploy Lambda Functions**:
   ```bash
   sam deploy --template-file template-lambda.yaml --stack-name bedrock-agent-lambda
   ```

4. **Upload sample data for testing**:
   ```bash
   python upload_samples.py --stack-name bedrock-agent-lambda
   ```

## 📋 Evaluation Output Structure

The Bedrock Agents implementation produces comprehensive evaluation data consistent with the other implementations:

```json
{
  "id": "candidate-uuid",
  "name": "Candidate Name",
  "resume_key": "resumes/candidate_resume.txt",
  "status": "completed",
  "job_title": "Senior AI Engineer",
  "evaluated_by": "bedrock-multi-agent",
  "evaluation_results": {
    "agent_collaboration_summary": {
      "supervisor": "HR Evaluation Coordinator",
      "collaborators": [
        "Resume Parser Agent",
        "Job Analyzer Agent",
        "Resume Evaluator Agent",
        "Candidate Rater Agent"
      ],
      "evaluation_approach": "Supervisor-collaborator multi-agent system"
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

### Bedrock Agents-Specific Monitoring
- **Agent Invocation Traces**: Detailed logs of agent interactions in Bedrock console
- **Multi-Agent Collaboration**: Monitor supervisor-collaborator communication
- **Agent Performance Metrics**: Track individual agent response times and success rates
- **Conversation Memory**: View agent context and state management

### AWS Service Monitoring
- **CloudWatch Logs**: Lambda function execution and agent invocation logs
- **DynamoDB Metrics**: Database performance and evaluation result storage
- **S3 Event Tracking**: Document upload and processing events
- **Bedrock Metrics**: Model usage, token consumption, and performance

### Debug Commands
```bash
# Check agent status
aws bedrock-agent get-agent --agent-id $SUPERVISOR_AGENT_ID

# List agent collaborators
aws bedrock-agent list-agent-collaborators --agent-id $SUPERVISOR_ID --agent-version DRAFT

# View recent Lambda logs
aws logs tail /aws/lambda/bedrock-agent-resume-processor-dev --region us-east-1 --follow

# Check evaluation results
aws dynamodb scan --table-name bedrock-agent-candidates-dev --region us-east-1 | jq '.Items[0]'
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
CANDIDATES_TABLE=bedrock-agent-candidates-dev
DOCUMENTS_BUCKET=bedrock-agent-documents-dev

# Bedrock Agents Configuration
SUPERVISOR_AGENT_ID=ABCDEFGHIJ
SUPERVISOR_AGENT_ALIAS_ID=TSTALIASID

# Model Configuration
MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
```

### Agent Configuration
```bash
# Supervisor Agent Instructions
SUPERVISOR_INSTRUCTIONS="You are the HR Evaluation Coordinator responsible for comprehensive resume evaluation..."

# Collaborator Agent Instructions
RESUME_PARSER_INSTRUCTIONS="You are the Resume Parser Agent specialized in extracting structured information..."
JOB_ANALYZER_INSTRUCTIONS="You are the Job Analyzer Agent specialized in analyzing job requirements..."
```

## 🚀 Advanced Features

### Dynamic Agent Collaboration
```python
# Supervisor Agent delegates to collaborators
response = bedrock_agent.invoke_agent(
    agentId=supervisor_agent_id,
    agentAliasId=supervisor_alias_id,
    sessionId=session_id,
    inputText=f"Evaluate this resume: {resume_text} against job: {job_description}"
)
```

### Agent Memory Management
```python
# Agents maintain conversation context
session_attributes = {
    "candidate_name": candidate_name,
    "job_title": job_title,
    "evaluation_stage": "comprehensive_analysis"
}
```

### Custom Agent Actions
```python
# Extend agent capabilities with custom actions
@agent_action
def calculate_skill_match(candidate_skills, required_skills):
    """Custom action for precise skill matching"""
    return skill_match_percentage
```

## 💰 Cost Optimization

### Bedrock Agents-Specific Optimizations
- **Agent Instruction Optimization**: Efficient prompts to reduce token usage
- **Collaboration Efficiency**: Minimize unnecessary agent-to-agent communication
- **Session Management**: Optimize conversation context and memory usage
- **Batch Processing**: Process multiple evaluations in single sessions

### AWS Service Optimizations
- **Lambda Memory Tuning**: Optimize memory allocation for agent invocation
- **DynamoDB Capacity**: Use on-demand billing for variable workloads
- **S3 Lifecycle Policies**: Manage document storage costs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch for your agent or collaboration pattern
3. Implement your changes with appropriate tests
4. Test multi-agent collaboration thoroughly
5. Submit a pull request with detailed description

## 📄 License

This project is licensed under the MIT License
