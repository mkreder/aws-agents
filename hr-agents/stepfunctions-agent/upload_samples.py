#!/usr/bin/env python3
import boto3
import os
import sys
import json
import argparse

def get_stack_outputs(stack_name, region='us-east-1'):
    """Get the outputs from a CloudFormation stack"""
    cfn = boto3.client('cloudformation', region_name=region)
    try:
        response = cfn.describe_stacks(StackName=stack_name)
        outputs = response['Stacks'][0]['Outputs']
        return {output['OutputKey']: output['OutputValue'] for output in outputs}
    except Exception as e:
        print(f"Error getting stack outputs: {e}")
        return None

def upload_samples(bucket_name, samples_dir='../samples'):
    """Upload sample files to the S3 bucket"""
    s3 = boto3.client('s3')
    
    # Check if samples directory exists
    if not os.path.isdir(samples_dir):
        print(f"Error: {samples_dir} directory not found")
        return False
    
    # Upload job descriptions
    jobs_dir = os.path.join(samples_dir, 'jobs')
    if os.path.isdir(jobs_dir):
        for filename in os.listdir(jobs_dir):
            file_path = os.path.join(jobs_dir, filename)
            if os.path.isfile(file_path):
                print(f"Uploading job description: {filename}")
                s3.upload_file(file_path, bucket_name, f"jobs/{filename}")
    
    # Upload resumes
    resumes_dir = os.path.join(samples_dir, 'resumes')
    if os.path.isdir(resumes_dir):
        for filename in os.listdir(resumes_dir):
            file_path = os.path.join(resumes_dir, filename)
            if os.path.isfile(file_path):
                print(f"Uploading resume: {filename}")
                s3.upload_file(file_path, bucket_name, f"resumes/{filename}")
    
    print(f"Sample files uploaded to s3://{bucket_name}/")
    return True

def main():
    parser = argparse.ArgumentParser(description='Upload sample files to S3 bucket')
    parser.add_argument('--stack-name', default='stepfunctions-agent', help='CloudFormation stack name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--samples-dir', default='../samples', help='Directory containing sample files')
    parser.add_argument('--bucket', help='S3 bucket name (if not provided, will be retrieved from stack outputs)')
    
    args = parser.parse_args()
    
    # Get bucket name from stack outputs if not provided
    bucket_name = args.bucket
    if not bucket_name:
        outputs = get_stack_outputs(args.stack_name, args.region)
        if not outputs:
            print("Failed to get stack outputs. Please provide bucket name with --bucket option.")
            sys.exit(1)
        
        bucket_name = outputs.get('DocumentsBucketName')
        if not bucket_name:
            print("DocumentsBucketName not found in stack outputs. Please provide bucket name with --bucket option.")
            sys.exit(1)
    
    # Upload sample files
    if upload_samples(bucket_name, args.samples_dir):
        print("Sample files uploaded successfully!")
    else:
        print("Failed to upload sample files.")
        sys.exit(1)

if __name__ == "__main__":
    main()