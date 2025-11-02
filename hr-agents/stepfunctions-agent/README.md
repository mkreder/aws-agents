# Step Functions HR Resume Evaluation System

This implementation demonstrates a workflow-based approach to building AI-powered HR resume evaluation systems using **AWS Step Functions**. This approach leverages Step Functions' orchestration capabilities with specialized Lambda functions working together through a visual state machine to provide comprehensive, structured resume evaluations.

## 🏗️ Architecture Overview

The Step Functions implementation uses a **sequential workflow orchestration** where specialized Lambda functions handle specific evaluation tasks. Each step in the process is clearly defined, monitored, and can be individually optimized, providing excellent visibility and control over the evaluation pipeline.

**Key Features:**
- **Visual Workflow Monitoring** - Clear step-by-step execution tracking
- **Specialized Lambda Functions** - Each evaluation task handled by dedicated function
- **Built-in Error Handling** - Automatic retry logic and failure management
- **Parallel Processing Capability** - Steps can be executed in parallel where appropriate

```
S3 Upload → Step Functions State Machine
                     ↓
┌─────────────────────────────────────────────────────────┐
│  Step Functions Workflow Orchestration                 │
│                                                         │
│  ┌─────────────────┐    ┌─────────────────┐           │
│  │ Resume Parser   │ →  │ Job Extractor   │           │
│  │ Lambda          │    │ Lambda          │           │
│  └─────────────────┘    └─────────────────┘           │
│           ↓                       ↓                    │
│  ┌─────────────────┐    ┌─────────────────┐           │
│  │ Resume Evaluator│ →  │ Gap Identifier  │           │
│  │ Lambda          │    │ Lambda          │           │
│  └─────────────────┘    └─────────────────┘           │
│           ↓                       ↓                    │
│  ┌─────────────────┐    ┌─────────────────┐           │
│  │ Candidate Rater │ →  │ Interview Notes │           │
│  │ Lambda          │    │ Generator Lambda│           │
│  └─────────────────┘    └─────────────────┘           │
└─────────────────────────────────────────────────────────┘
                              ↓
                         DynamoDB Storage
```

## 🚀 Key Features

### Step Functions-Specific Advantages

- **Visual Workflow Tracking**: Real-time execution monitoring with step-by-step visibility
- **Built-in Error Handling**: Automatic retry mechanisms and failure recovery
- **State Management**: Explicit state passing between workflow steps
- **Parallel Execution**: Ability to run independent steps simultaneously
- **Audit Trail**: Complete execution history and debugging capabilities

### Core Capabilities

- **Automated Resume Processing** - Upload resumes to S3 for automatic evaluation
- **Workflow Orchestration** - Step Functions manages the entire evaluation pipeline
- **Comprehensive Analysis** - Skills, experience, education, and cultural fit assessment
- **Gap Identification** - Identifies missing skills and experience gaps
- **Candidate Rating** - Numerical scoring with detailed justification
- **Interview Preparation** - Generates structured interview questions
- **Structured Data Storage** - Results stored in DynamoDB with consistent schema

## 🛠️ Technology Stack

### Core Services
- **AWS Step Functions** - Workflow orchestration and state management
- **Amazon Bedrock** - Claude Sonnet 3.7 for enhanced AI processing
- **AWS Lambda** - Serverless compute for specialized evaluation tasks
- **Amazon S3** - Document storage and event triggers
- **Amazon DynamoDB** - NoSQL database for evaluation results
- **AWS IAM** - Identity and access management

### Step Functions Components
- **State Machine** - Visual workflow definition and execution
- **Lambda Integration** - Seamless function invocation and data passing
- **Error Handling** - Built-in retry and catch mechanisms
- **CloudWatch Integration** - Comprehensive monitoring and logging

## 📁 Project Structure

```
stepfunctions-agent/
├── README.md                   # This file
├── template.yaml              # SAM template with all resources
├── deploy.sh                  # Automated deployment script
├── cleanup.sh                 # Resource cleanup script
├── upload_samples.py          # Sample data upload utility
├── functions/                 # Lambda function source code
│   ├── resume_parser/         # Resume parsing logic
│   ├── job_extractor/         # Job analysis logic
│   ├── evaluate_resume/       # Resume evaluation logic
│   ├── identify_gaps/         # Gap analysis logic
│   ├── rate_candidate/        # Candidate rating logic
│   └── generate_interview_notes/ # Interview preparation logic
└── statemachine/              # Step Functions definition
    └── resume_evaluation.asl.json
```

## 🔄 Workflow Steps

The Step Functions state machine processes resumes through these specialized stages:

### 1. Resume Parser Lambda
**Purpose**: Extracts structured information from resume text
**Input**: Raw resume content from S3
**Output**: Structured personal info, experience, education, skills
**Model**: Claude Sonnet 3.7 for accurate text parsing

### 2. Job Extractor Lambda
**Purpose**: Analyzes job descriptions and requirements
**Input**: Job description from S3
**Output**: Required/preferred skills, experience levels, qualifications
**Model**: Claude Sonnet 3.7 for requirement analysis

### 3. Resume Evaluator Lambda
**Purpose**: Evaluates candidate fit against job requirements
**Input**: Parsed resume + job requirements
**Output**: Skills match analysis, experience relevance, education alignment
**Model**: Claude Sonnet 3.7 for comprehensive evaluation

### 4. Gap Identifier Lambda
**Purpose**: Identifies skill and experience gaps
**Input**: Evaluation results
**Output**: Missing skills, experience gaps, areas of concern
**Model**: Claude Sonnet 3.7 for gap analysis

### 5. Candidate Rater Lambda
**Purpose**: Provides numerical rating with justification
**Input**: Complete evaluation data
**Output**: 1-5 rating scale with detailed reasoning and strengths/weaknesses
**Model**: Claude Sonnet 3.7 for objective scoring

### 6. Interview Notes Generator Lambda
**Purpose**: Creates structured interview preparation materials
**Input**: Complete candidate profile
**Output**: Technical questions, behavioral questions, focus areas
**Model**: Claude Sonnet 3.7 for interview preparation

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- AWS SAM CLI installed
- Python 3.11 or later
- Access to Amazon Bedrock Claude Sonnet 3.7 model

### Deployment

1. **Navigate to the Step Functions implementation**:
   ```bash
   cd stepfunctions-agent
   ```

2. **Deploy the complete system**:
   ```bash
   ./deploy.sh
   ```

   The deployment script will:
   - Deploy Step Functions state machine
   - Deploy all Lambda functions
   - Configure S3 bucket and DynamoDB table
   - Set up IAM roles and permissions

3. **Upload sample data for testing**:
   ```bash
   # Upload job description
   aws s3 cp ../samples/jobs/ai_engineer_position.txt s3://stepfunctions-agent-documents-dev/jobs/
   
   # Upload resume (triggers processing)
   aws s3 cp ../samples/resumes/john_doe_ai_engineer.txt s3://stepfunctions-agent-documents-dev/resumes/
   ```

4. **Monitor processing**:
   ```bash
   # View Step Functions execution
   aws stepfunctions list-executions --state-machine-arn <state-machine-arn>
   
   # Check results
   aws dynamodb scan --table-name stepfunctions-agent-candidates-dev --region us-east-1
   ```

## 📋 Evaluation Output Structure

The Step Functions implementation produces comprehensive evaluation data consistent with the other implementations:

```json
{
  "id": "candidate-uuid",
  "name": "Candidate Name",
  "resume_key": "resumes/candidate_resume.txt",
  "status": "completed",
  "job_title": "Senior AI Engineer",
  "evaluated_by": "stepfunctions-workflow",
  "evaluation_results": {
    "workflow_summary": {
      "orchestrator": "AWS Step Functions",
      "steps_completed": [
        "Resume Parser",
        "Job Extractor",
        "Resume Evaluator",
        "Gap Identifier",
        "Candidate Rater",
        "Interview Notes Generator"
      ],
      "execution_approach": "Sequential workflow orchestration"
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

### Step Functions-Specific Monitoring
- **Visual Execution Tracking**: Real-time workflow progress in Step Functions console
- **Step-by-Step Analysis**: Individual Lambda function success/failure status
- **Input/Output Inspection**: Data flow between workflow steps
- **Performance Metrics**: Execution duration and timing analysis

### AWS Service Monitoring
- **CloudWatch Logs**: Individual Lambda function execution logs
- **DynamoDB Metrics**: Database performance and data storage
- **S3 Event Tracking**: Document upload and processing events
- **Lambda Metrics**: Function duration, memory usage, and error rates

### Debug Commands
```bash
# Monitor Step Functions execution
aws stepfunctions describe-execution --execution-arn <execution-arn>

# View specific Lambda function logs
aws logs tail /aws/lambda/stepfunctions-resume-parser-dev --region us-east-1 --follow

# Check evaluation results
aws dynamodb scan --table-name stepfunctions-agent-candidates-dev --region us-east-1 | jq '.Items[0]'

# List recent executions
aws stepfunctions list-executions --state-machine-arn <state-machine-arn> --max-items 5
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
CANDIDATES_TABLE=stepfunctions-agent-candidates-dev
DOCUMENTS_BUCKET=stepfunctions-agent-documents-dev

# Step Functions Configuration
STATE_MACHINE_ARN=arn:aws:states:us-east-1:account:stateMachine:ResumeEvaluationWorkflow

# Model Configuration
MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
```

### Workflow Configuration
```json
{
  "Comment": "Resume evaluation workflow",
  "StartAt": "ParseResume",
  "States": {
    "ParseResume": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:account:function:resume-parser",
      "Next": "ExtractJobRequirements"
    }
  }
}
```

## 🚀 Advanced Features

### Parallel Processing
```json
{
  "Type": "Parallel",
  "Branches": [
    {
      "StartAt": "ParseResume",
      "States": { /* Resume parsing branch */ }
    },
    {
      "StartAt": "ExtractJob",
      "States": { /* Job analysis branch */ }
    }
  ]
}
```

### Error Handling
```json
{
  "Type": "Task",
  "Resource": "arn:aws:lambda:function:resume-parser",
  "Retry": [
    {
      "ErrorEquals": ["States.TaskFailed"],
      "IntervalSeconds": 2,
      "MaxAttempts": 3
    }
  ],
  "Catch": [
    {
      "ErrorEquals": ["States.ALL"],
      "Next": "HandleError"
    }
  ]
}
```

### Conditional Logic
```json
{
  "Type": "Choice",
  "Choices": [
    {
      "Variable": "$.candidateRating",
      "NumericGreaterThan": 4,
      "Next": "HighPriorityInterview"
    }
  ],
  "Default": "StandardInterview"
}
```

## 💰 Cost Optimization

### Step Functions-Specific Optimizations
- **State Transitions**: Minimize unnecessary state transitions
- **Parallel Processing**: Execute independent steps simultaneously
- **Express Workflows**: Use for high-volume, short-duration workflows
- **Standard Workflows**: Use for complex, long-running processes

### AWS Service Optimizations
- **Lambda Memory Tuning**: Optimize memory allocation for each function
- **DynamoDB Capacity**: Use on-demand billing for variable workloads
- **S3 Lifecycle Policies**: Manage document storage costs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch for your workflow step
3. Implement your changes with appropriate tests
4. Update Step Functions state machine definition
5. Submit a pull request with detailed description

## 📄 License

This project is licensed under the MIT License
