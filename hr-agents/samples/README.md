# Sample S3 Structure for Recruitment Agent

This directory represents the expected structure of the S3 bucket used by the recruitment agent application. The S3 bucket (`${AWS::StackName}-documents-${Environment}`) is organized into two main directories:

## Directory Structure

```
${AWS::StackName}-documents-${Environment}/
├── jobs/
│   └── ai_engineer_position.txt    # Sample job description
└── resumes/
    └── john_doe_resume.txt         # Sample candidate resume
```

## Prefixes and Their Purpose

### Jobs Prefix (`jobs/`)
- Contains job descriptions in text format
- Used by the `JobExtractorFunction` to analyze and extract job requirements
- Naming convention: descriptive name of the position (e.g., `ai_engineer_position.txt`)
- Files should be in plain text format for optimal processing

### Resumes Prefix (`resumes/`)
- Contains candidate resumes in text format
- Processed by the `ResumeParserFunction` to extract candidate information
- Naming convention: candidate name or identifier (e.g., `john_doe_resume.txt`)
- Files should be in plain text format for optimal processing

## File Processing Flow

1. When a new job description is uploaded to the `jobs/` prefix:
   - The `JobExtractorFunction` processes it
   - Requirements are extracted and stored in the `JobsTable` DynamoDB table

2. When a new resume is uploaded to the `resumes/` prefix:
   - The `ResumeParserFunction` processes it
   - Candidate information is extracted and stored in the `CandidatesTable`
   - The recruitment workflow is triggered through Step Functions

## Sample Files

The provided sample files demonstrate the expected format and content for:
- A job description for an AI Engineer position
- A candidate's resume applying for that position

These samples can be used to test the recruitment agent's functionality and understand the expected input format. 