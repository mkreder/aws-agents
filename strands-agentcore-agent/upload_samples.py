#!/usr/bin/env python3
"""
Upload sample resumes and job descriptions to test the AgentCore implementation.
"""

import boto3
import os
import sys

def main():
    # Get bucket name from environment or CloudFormation
    try:
        # Try to get from CloudFormation stack
        cf_client = boto3.client('cloudformation', region_name='us-east-1')
        stack_name = 'hr-agents-strands-agentcore'
        
        response = cf_client.describe_stacks(StackName=stack_name)
        outputs = response['Stacks'][0]['Outputs']
        
        bucket_name = None
        for output in outputs:
            if output['OutputKey'] == 'DocumentsBucket':
                bucket_name = output['OutputValue']
                break
        
        if not bucket_name:
            print("❌ Could not find DocumentsBucket in CloudFormation outputs")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error getting bucket name from CloudFormation: {e}")
        sys.exit(1)
    
    print(f"📦 Uploading samples to bucket: {bucket_name}")
    
    # Initialize S3 client
    s3_client = boto3.client('s3', region_name='us-east-1')
    
    # Sample job description
    job_description = """
Senior Software Engineer - AI/ML Platform

We are seeking a Senior Software Engineer to join our AI/ML Platform team. You will be responsible for building and maintaining scalable machine learning infrastructure and developing AI-powered applications.

Requirements:
- Bachelor's degree in Computer Science or related field
- 5+ years of software engineering experience
- Strong proficiency in Python and modern frameworks
- Experience with cloud platforms (AWS, GCP, or Azure)
- Knowledge of machine learning frameworks (TensorFlow, PyTorch, or similar)
- Experience with containerization (Docker, Kubernetes)
- Familiarity with CI/CD pipelines and DevOps practices

Preferred Qualifications:
- Master's degree in Computer Science or AI/ML
- Experience with distributed systems and microservices
- Knowledge of data engineering and ETL pipelines
- Experience with monitoring and observability tools
- Contributions to open-source projects

Responsibilities:
- Design and implement scalable ML infrastructure
- Develop AI-powered applications and services
- Collaborate with data scientists and ML engineers
- Optimize system performance and reliability
- Mentor junior engineers and contribute to technical decisions

We offer competitive compensation, comprehensive benefits, and the opportunity to work on cutting-edge AI technology in a collaborative environment.
"""
    
    # Sample resume
    resume_content = """
John Smith
Senior Software Engineer
Email: john.smith@email.com
Phone: (555) 123-4567
Location: San Francisco, CA
LinkedIn: linkedin.com/in/johnsmith

PROFESSIONAL SUMMARY
Experienced Senior Software Engineer with 6+ years of expertise in building scalable web applications and machine learning systems. Proven track record of leading technical initiatives and mentoring development teams. Strong background in Python, cloud technologies, and AI/ML frameworks.

WORK EXPERIENCE

Senior Software Engineer | TechCorp Inc. | 2021 - Present
• Led development of ML platform serving 10M+ daily requests with 99.9% uptime
• Implemented automated CI/CD pipelines reducing deployment time by 75%
• Architected microservices infrastructure using Docker and Kubernetes
• Mentored 3 junior engineers and conducted technical interviews
• Technologies: Python, FastAPI, PostgreSQL, Redis, AWS, Docker, Kubernetes

Software Engineer | DataSolutions LLC | 2019 - 2021
• Developed data processing pipelines handling 1TB+ daily data volume
• Built RESTful APIs and web applications using Python and React
• Implemented monitoring and alerting systems improving incident response by 60%
• Collaborated with data science team on ML model deployment
• Technologies: Python, Django, React, MySQL, Apache Airflow, GCP

Junior Software Engineer | StartupXYZ | 2018 - 2019
• Contributed to full-stack web application development
• Implemented automated testing increasing code coverage to 85%
• Participated in agile development processes and code reviews
• Technologies: Python, Flask, JavaScript, MongoDB

EDUCATION

Bachelor of Science in Computer Science | University of California, Berkeley | 2018
• Relevant Coursework: Machine Learning, Data Structures, Algorithms, Database Systems
• Senior Project: Built recommendation system using collaborative filtering
• GPA: 3.7/4.0

TECHNICAL SKILLS

Programming Languages: Python, JavaScript, SQL, Java, Go
Frameworks: FastAPI, Django, Flask, React, TensorFlow, PyTorch
Cloud Platforms: AWS (EC2, S3, Lambda, RDS), GCP (Compute Engine, BigQuery)
Tools & Technologies: Docker, Kubernetes, Git, Jenkins, Apache Airflow, Redis
Databases: PostgreSQL, MySQL, MongoDB, Redis

PROJECTS

ML Platform Infrastructure (2022-2023)
• Designed and implemented scalable ML inference platform
• Reduced model serving latency by 40% through optimization
• Implemented A/B testing framework for model evaluation
• Technologies: Python, FastAPI, Docker, Kubernetes, AWS

Real-time Analytics Dashboard (2021)
• Built real-time data visualization dashboard for business metrics
• Processed streaming data using Apache Kafka and Apache Spark
• Implemented caching layer reducing query response time by 70%
• Technologies: Python, React, Apache Kafka, Apache Spark, Redis

CERTIFICATIONS
• AWS Certified Solutions Architect - Associate (2022)
• Certified Kubernetes Administrator (CKA) (2021)
"""
    
    try:
        # Upload job description
        print("📄 Uploading job description...")
        s3_client.put_object(
            Bucket=bucket_name,
            Key='jobs/senior_software_engineer.txt',
            Body=job_description.encode('utf-8'),
            ContentType='text/plain'
        )
        print("✅ Job description uploaded")
        
        # Upload sample resume
        print("📄 Uploading sample resume...")
        s3_client.put_object(
            Bucket=bucket_name,
            Key='resumes/john_smith.txt',
            Body=resume_content.encode('utf-8'),
            ContentType='text/plain'
        )
        print("✅ Sample resume uploaded")
        
        print("")
        print("🎉 Sample files uploaded successfully!")
        print(f"📦 Bucket: {bucket_name}")
        print("📁 Files:")
        print("  - jobs/senior_software_engineer.txt")
        print("  - resumes/john_smith.txt")
        print("")
        print("🔄 The resume should be automatically processed by the AgentCore agent.")
        print("📊 Check the DynamoDB table for results in a few minutes.")
        
    except Exception as e:
        print(f"❌ Error uploading files: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
