# HR AI Agents - Strands AgentCore Implementation

This implementation demonstrates building AI-powered HR resume evaluation systems using Amazon Bedrock AgentCore Runtime with Strands Agents SDK. It provides the same comprehensive candidate assessment as the Lambda version but runs on AgentCore's serverless runtime.

## 🏗️ Architecture Overview

This implementation uses:
- **Amazon Bedrock AgentCore Runtime** - Serverless runtime for hosting Strands agents
- **Strands Agents SDK** - Multi-agent collaboration framework
- **Amazon S3** - Resume and job description storage with event triggers
- **Amazon DynamoDB** - Evaluation results storage
- **AWS Lambda** - S3 event processing and AgentCore invocation

## 🚀 Key Features

- **AgentCore Runtime Hosting** - Agents run in secure, isolated microVM sessions
- **Multi-Agent Collaboration** - Specialized agents work together naturally
- **S3 Event Integration** - Automatic processing when resumes are uploaded
- **Structured JSON Output** - Consistent evaluation format
- **Extended Processing Time** - AgentCore supports longer-running evaluations
- **Enterprise Security** - Built-in identity and access management

## 📊 Agent Architecture

### HR Supervisor Agent
Coordinates the evaluation process and manages specialized collaborator agents:

1. **ResumeParserAgent** - Extracts structured information from resumes
2. **JobAnalyzerAgent** - Analyzes job requirements and qualifications
3. **ResumeEvaluatorAgent** - Evaluates candidate fit against job requirements
4. **GapIdentifierAgent** - Identifies missing qualifications and gaps
5. **CandidateRaterAgent** - Provides numerical rating (1-5) with justification
6. **InterviewNotesAgent** - Generates interview preparation materials

## 🛠️ Technology Stack

- **Amazon Bedrock AgentCore Runtime** - Agent hosting platform
- **Strands Agents SDK** - Agent framework and collaboration
- **AWS Lambda** - Event processing and AgentCore invocation
- **Amazon S3** - Document storage and event triggers
- **Amazon DynamoDB** - NoSQL database for results
- **Amazon Bedrock** - AI/ML models (Claude 3.5 Sonnet)
- **AWS IAM** - Identity and access management

## 📁 Project Structure

```
strands-agentcore-agent/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── bedrock_agentcore.yaml      # AgentCore configuration (generated)
├── hr_agent.py                 # Main Strands agent code
├── s3_processor.py             # Lambda function for S3 events
├── template-infrastructure.yaml # Infrastructure resources
├── template-lambda.yaml        # Lambda function template
├── deploy.sh                   # Deployment script
└── .gitignore                  # Git ignore file
```

## 🚀 Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.10+ installed
- Access to Amazon Bedrock models in your region
- AgentCore permissions configured

### Installation

1. **Install required packages:**
```bash
pip install --upgrade pip
pip install bedrock-agentcore strands-agents bedrock-agentcore-starter-toolkit boto3
```

2. **Deploy infrastructure:**
```bash
./deploy.sh
```

3. **Test the agent:**
```bash
# Upload sample files
python upload_samples.py

# Check results in DynamoDB
aws dynamodb scan --table-name hr-agents-candidates-agentcore
```

## 🔧 Deployment Process

The deployment script performs these steps:

1. **Deploy Infrastructure** - Creates S3 bucket, DynamoDB table, and IAM roles
2. **Configure AgentCore** - Sets up agent configuration for runtime
3. **Deploy Agent** - Containerizes and deploys agent to AgentCore Runtime
4. **Deploy Lambda** - Creates S3 event processor function
5. **Configure Triggers** - Sets up S3 event notifications

## 📋 Usage

1. **Upload job descriptions** to S3 bucket under `jobs/` prefix
2. **Upload resumes** to S3 bucket under `resumes/` prefix
3. **S3 events trigger Lambda** which invokes the AgentCore agent
4. **Agent processes resume** using multi-agent collaboration
5. **Results stored** in DynamoDB with structured evaluation data

## 📊 Sample Output Structure

```json
{
  "id": "candidate-uuid",
  "resume_key": "resumes/john_doe.txt",
  "name": "John Doe",
  "status": "completed",
  "evaluated_by": "Strands AgentCore Multi-Agent System",
  "agentcore_metadata": {
    "agent_arn": "arn:aws:bedrock-agentcore:...",
    "session_id": "session-uuid",
    "runtime_version": "1.0"
  },
  "resume_parsing": {
    "personal_info": {...},
    "experience": [...],
    "education": [...],
    "skills": {...}
  },
  "job_analysis": {...},
  "resume_evaluation": {...},
  "gap_analysis": {...},
  "candidate_rating": {
    "rating": 4,
    "justification": "...",
    "strengths": [...],
    "weaknesses": [...]
  },
  "interview_notes": {
    "questions": [...],
    "focus_areas": [...],
    "talking_points": [...]
  }
}
```

## 🔍 Monitoring & Debugging

- **AgentCore Observability** - Built-in tracing and monitoring
- **CloudWatch Logs** - Detailed execution logs
- **CloudWatch Transaction Search** - Agent interaction tracing
- **DynamoDB Console** - View evaluation results
- **S3 Event Logs** - Monitor file processing

## 🛡️ Security Features

- **Isolated Execution** - Each agent runs in secure microVM
- **IAM Integration** - Fine-grained access controls
- **Encrypted Storage** - S3 and DynamoDB encryption
- **VPC Support** - Optional private networking
- **Audit Logging** - CloudTrail integration

## 💰 Cost Considerations

- **Consumption-based Pricing** - Pay only for agent invocations
- **No Infrastructure Management** - Serverless scaling
- **Efficient Resource Usage** - Optimized for agentic workloads
- **Token Usage Monitoring** - Track Bedrock model costs

## 🔄 Differences from Lambda Implementation

| Feature | Lambda Implementation | AgentCore Implementation |
|---------|----------------------|-------------------------|
| **Runtime** | AWS Lambda (15 min limit) | AgentCore Runtime (extended) |
| **Scaling** | Lambda concurrency | AgentCore auto-scaling |
| **Cold Starts** | Standard Lambda | Optimized for agents |
| **Session Management** | Stateless | Session isolation |
| **Observability** | CloudWatch Logs | Built-in agent tracing |
| **Identity** | IAM roles | AgentCore Identity |
| **Deployment** | SAM/CloudFormation | AgentCore Starter Toolkit |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test with AgentCore locally
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**AgentCore Benefits:**
- **Enterprise-grade Security** - Built-in identity and access management
- **Optimized for Agents** - Purpose-built runtime for agentic workloads
- **Framework Flexibility** - Works with any Python agent framework
- **Advanced Observability** - Comprehensive monitoring and tracing
