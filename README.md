# HR AI Agents - Automated Resume Evaluation System

This repository demonstrates three different approaches to building AI-powered HR resume evaluation systems using AWS services. All implementations provide comprehensive candidate assessment including resume parsing, skills analysis, gap identification, candidate rating, and interview preparation.

## 🏗️ Architecture Approaches

### Step Functions Implementation (`stepfunctions-agent/`)
A workflow-based approach using AWS Step Functions to orchestrate multiple specialized Lambda functions, each handling a specific aspect of resume evaluation.

### Bedrock Agent Implementation (`bedrock-agent/`)
A multi-agent AI approach using Amazon Bedrock Agents with collaborative AI agents that work together to provide comprehensive resume evaluations.

### Strands Multi-Agent Implementation (`strands-agent/`)
A natural collaboration approach using Strands Agents SDK where specialized agents communicate in natural language to provide adaptive, comprehensive resume evaluations.

## 🚀 Key Features

- **Automated Resume Processing** - Upload resumes to S3 and get automatic evaluations
- **Comprehensive Analysis** - Skills assessment, experience evaluation, and education review
- **Gap Identification** - Identifies missing skills and experience gaps
- **Candidate Rating** - Numerical scoring (1-5 scale) with detailed justification
- **Interview Preparation** - Generates structured interview questions and talking points
- **Structured Data Storage** - All results stored in DynamoDB with consistent schema

## 📊 Evaluation Components

All implementations provide:

1. **Resume Parsing** - Extract structured information from resume text
2. **Skills Analysis** - Identify technical and soft skills
3. **Experience Assessment** - Evaluate relevant work experience
4. **Education Review** - Assess educational background and certifications
5. **Job Matching** - Compare candidate profile against job requirements
6. **Gap Analysis** - Identify areas where candidate may need development
7. **Candidate Rating** - Numerical score with strengths and weaknesses
8. **Interview Notes** - Structured questions and areas to explore

## 🛠️ Technology Stack

### Common Services
- **Amazon Bedrock** - AI/ML models for natural language processing
- **AWS Lambda** - Serverless compute for processing logic
- **Amazon S3** - Document storage and event triggers
- **Amazon DynamoDB** - NoSQL database for evaluation results
- **AWS IAM** - Identity and access management

### Step Functions Specific
- **AWS Step Functions** - Workflow orchestration
- **Multiple Lambda Functions** - Specialized processing steps

### Bedrock Agent Specific
- **Amazon Bedrock Agents** - Multi-agent AI collaboration
- **Agent Collaboration** - Supervisor-collaborator pattern

### Strands Agent Specific
- **Strands Agents SDK** - Natural language agent collaboration
- **Multi-Agent Swarm** - Dynamic agent coordination
- **Custom Tools** - Specialized HR evaluation tools
- **15-Minute Processing** - Extended timeout for comprehensive evaluations
- **Structured JSON Output** - Consistent data format across implementations

## 📁 Project Structure

```
hr-agents/
├── README.md                    # This file
├── stepfunctions-agent/         # Step Functions implementation
│   ├── README.md               # Step Functions specific documentation
│   ├── template.yaml           # SAM template
│   ├── deploy.sh               # Automated deployment script
│   ├── functions/              # Lambda function code
│   └── statemachine/           # Step Functions definition
├── bedrock-agent/              # Bedrock Agent implementation
│   ├── README.md               # Bedrock Agent specific documentation
│   ├── template-agents-phase1.yaml  # Bedrock Agents template
│   ├── template-lambda.yaml    # Lambda functions template
│   ├── deploy.sh               # Automated deployment script
│   └── functions/              # Lambda function code
├── strands-agent/              # Strands Agent implementation
│   ├── README.md               # Strands Agent specific documentation
│   ├── template-infrastructure.yaml # Infrastructure resources (S3, DynamoDB)
│   ├── template-lambda.yaml    # Lambda functions and layer template
│   ├── deploy.sh               # Automated deployment script
│   ├── create_lambda_package.py # Lambda packaging with proper layer structure
│   └── functions/              # Lambda function code
└── samples/                    # Sample data for testing
    ├── jobs/                   # Sample job descriptions
    └── resumes/                # Sample resumes
```

## 🚀 Quick Start

### Step Functions Implementation

```bash
cd stepfunctions-agent
./deploy.sh
python upload_samples.py
```

### Bedrock Agent Implementation

```bash
cd bedrock-agent
./deploy.sh
```

### Strands Agent Implementation

```bash
cd strands-agent
./deploy.sh
```

## 📋 Prerequisites

- AWS CLI configured with appropriate permissions
- AWS SAM CLI installed
- Python 3.11 or later
- Access to Amazon Bedrock models in your AWS region

## 🔧 Usage

1. **Deploy** your chosen implementation
2. **Upload job descriptions** to the S3 bucket under `jobs/` prefix
3. **Upload resumes** to the S3 bucket under `resumes/` prefix
4. **Monitor processing** through CloudWatch logs
5. **View results** in the DynamoDB candidates table

## 📊 Sample Output

Both implementations produce structured evaluation data including:

- **Candidate Information** - Name, contact details, resume summary
- **Skills Assessment** - Programming languages, frameworks, tools
- **Experience Analysis** - Years of experience, relevant roles, achievements
- **Education Evaluation** - Degrees, institutions, alignment with role
- **Rating & Recommendation** - Numerical score and hiring recommendation
- **Interview Preparation** - Suggested questions and areas to explore

## 🔍 Monitoring & Debugging

- **CloudWatch Logs** - Detailed execution logs for all components
- **DynamoDB Console** - View processed candidate evaluations
- **Step Functions Console** - Visual workflow execution (Step Functions implementation)
- **Bedrock Console** - Agent invocation traces (Bedrock Agent implementation)

## 🛡️ Security Considerations

- Resume data contains PII - ensure proper encryption and access controls
- Use IAM roles with least-privilege access
- Enable CloudTrail for audit logging
- Consider VPC endpoints for private communication

## 💰 Cost Optimization

- Monitor Bedrock token usage and optimize prompts
- Use appropriate Lambda memory settings
- Consider reserved capacity for high-volume DynamoDB usage
- Implement lifecycle policies for S3 storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License 

## 🆘 Support

For questions and support:
- Check the implementation-specific README files
- Review CloudWatch logs for debugging
- Consult AWS documentation for service-specific issues

---

**Choose Your Implementation:**
- **Step Functions** for complex workflows with detailed monitoring
- **Bedrock Agents** for AI-native multi-agent collaboration
- **Strands Agents** for natural language agent collaboration with maximum flexibility

All three approaches provide identical functionality with different architectural patterns!