#!/usr/bin/env python3

import boto3
import os
import argparse
from pathlib import Path

def get_bucket_name(stack_name):
    """Get the S3 bucket name from CloudFormation stack outputs"""
    cf_client = boto3.client('cloudformation')
    
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
        
        for output in stack.get('Outputs', []):
            if output['OutputKey'] == 'DocumentsBucketName':
                return output['OutputValue']
        
        raise ValueError(f"DocumentsBucketName output not found in stack {stack_name}")
    
    except Exception as e:
        print(f"Error getting bucket name from stack {stack_name}: {e}")
        return None

def upload_files_to_s3(bucket_name, local_dir, s3_prefix):
    """Upload files from local directory to S3 with given prefix"""
    s3_client = boto3.client('s3')
    
    local_path = Path(local_dir)
    if not local_path.exists():
        print(f"Local directory {local_dir} does not exist")
        return False
    
    uploaded_files = []
    
    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            # Calculate relative path from the local directory
            relative_path = file_path.relative_to(local_path)
            s3_key = f"{s3_prefix}/{relative_path}".replace('\\', '/')
            
            try:
                print(f"Uploading {file_path} to s3://{bucket_name}/{s3_key}")
                s3_client.upload_file(str(file_path), bucket_name, s3_key)
                uploaded_files.append(s3_key)
            except Exception as e:
                print(f"Error uploading {file_path}: {e}")
                return False
    
    return uploaded_files

def main():
    parser = argparse.ArgumentParser(description='Upload sample files to S3 bucket')
    parser.add_argument('--stack-name', default='bedrock-agent-lambda',
                       help='CloudFormation stack name (default: bedrock-agent-lambda)')
    parser.add_argument('--bucket', help='S3 bucket name (if not using stack name)')
    parser.add_argument('--samples-dir', default='../samples',
                       help='Directory containing sample files (default: ../samples - root samples folder)')
    
    args = parser.parse_args()
    
    # Get bucket name
    if args.bucket:
        bucket_name = args.bucket
    else:
        bucket_name = get_bucket_name(args.stack_name)
        if not bucket_name:
            print("Failed to get bucket name. Please specify --bucket directly.")
            return 1
    
    print(f"Using bucket: {bucket_name}")
    
    # Check if samples directory exists
    samples_dir = Path(args.samples_dir)
    if not samples_dir.exists():
        print(f"Samples directory {samples_dir} does not exist")
        print("Please create sample files or adjust the --samples-dir path")
        return 1
    
    # Upload job descriptions
    jobs_dir = samples_dir / 'jobs'
    if jobs_dir.exists():
        print("\n📄 Uploading job descriptions...")
        job_files = upload_files_to_s3(bucket_name, str(jobs_dir), 'jobs')
        if job_files:
            print(f"✅ Uploaded {len(job_files)} job description(s)")
        else:
            print("❌ Failed to upload job descriptions")
            return 1
    else:
        print(f"⚠️  Jobs directory {jobs_dir} not found, skipping job descriptions")
    
    # Upload resumes
    resumes_dir = samples_dir / 'resumes'
    if resumes_dir.exists():
        print("\n📋 Uploading sample resumes...")
        resume_files = upload_files_to_s3(bucket_name, str(resumes_dir), 'resumes')
        if resume_files:
            print(f"✅ Uploaded {len(resume_files)} resume(s)")
            print("\n🎉 Sample files uploaded successfully!")
            print(f"\nThe Lambda function will automatically process resumes uploaded to the 'resumes/' prefix.")
            print(f"Check CloudWatch logs for the agent's evaluation results.")
        else:
            print("❌ Failed to upload resumes")
            return 1
    else:
        print(f"⚠️  Resumes directory {resumes_dir} not found, skipping resumes")
    
    return 0

if __name__ == '__main__':
    exit(main())
