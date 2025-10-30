#!/usr/bin/env python3
"""
MinIO Bucket Setup Script
Creates buckets and configures access policies for INSA CRM file storage
"""

import logging
from minio import Minio
from minio.error import S3Error
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MinIO connection config
MINIO_ENDPOINT = "localhost:9200"
MINIO_ACCESS_KEY = "insa_admin"
MINIO_SECRET_KEY = "110811081108"

# Buckets to create
BUCKETS = [
    {
        "name": "insa-projects",
        "description": "Project files (private by default)",
        "policy": "private"
    },
    {
        "name": "insa-shared",
        "description": "Shared files (team access)",
        "policy": "private"
    },
    {
        "name": "insa-public",
        "description": "Public files (read-only for all)",
        "policy": "download"  # Public read-only
    },
    {
        "name": "insa-ai-generated",
        "description": "Files created by AI agents",
        "policy": "private"
    }
]

def create_buckets():
    """Create MinIO buckets with policies"""

    logger.info("=" * 60)
    logger.info("MinIO Bucket Setup for INSA CRM")
    logger.info("=" * 60)

    # Initialize MinIO client
    logger.info(f"Connecting to MinIO at {MINIO_ENDPOINT}...")
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False  # HTTP (not HTTPS) for local
    )

    # Test connection
    try:
        client.list_buckets()
        logger.info("Connected to MinIO successfully")
    except S3Error as e:
        logger.error(f"Failed to connect to MinIO: {e}")
        return False

    # Create buckets
    for bucket_config in BUCKETS:
        bucket_name = bucket_config["name"]
        description = bucket_config["description"]
        policy_type = bucket_config["policy"]

        logger.info(f"Creating bucket: {bucket_name}")
        logger.info(f"Description: {description}")

        try:
            # Check if bucket already exists
            if client.bucket_exists(bucket_name):
                logger.warning(f"Bucket already exists, skipping: {bucket_name}")
            else:
                # Create bucket
                client.make_bucket(bucket_name)
                logger.info(f"Bucket created successfully: {bucket_name}")

            # Set bucket policy
            if policy_type == "download":
                # Public read-only policy
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": ["*"]},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                        }
                    ]
                }
                client.set_bucket_policy(bucket_name, json.dumps(policy))
                logger.info(f"Public read policy applied to {bucket_name}")
            else:
                logger.info(f"Private policy (default) for {bucket_name}")

        except S3Error as e:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            return False

    # List all buckets
    logger.info("=" * 60)
    logger.info("All MinIO Buckets:")
    logger.info("=" * 60)
    buckets = client.list_buckets()
    for bucket in buckets:
        logger.info(f"• {bucket.name} (created: {bucket.creation_date})")

    logger.info("MinIO bucket setup complete!")
    logger.info(f"MinIO Web Console: http://localhost:9201")
    logger.info(f"Username: {MINIO_ACCESS_KEY}")
    logger.info(f"Password: {MINIO_SECRET_KEY}")
    logger.info(f"MinIO API Endpoint: http://localhost:9200")

    return True

def test_upload_download():
    """Test basic upload and download"""

    logger.info("=" * 60)
    logger.info("Testing Upload/Download")
    logger.info("=" * 60)

    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

    # Create test file
    test_file = "/tmp/minio_test_file.txt"
    test_content = "INSA CRM MinIO Test File\nCreated: 2025-10-20\n"

    with open(test_file, "w") as f:
        f.write(test_content)

    bucket_name = "insa-projects"
    object_name = "test/test_file.txt"

    try:
        # Upload
        logger.info(f"Uploading test file to {bucket_name}/{object_name}...")
        client.fput_object(bucket_name, object_name, test_file)
        logger.info("Upload successful")

        # Check if exists
        logger.info("Checking if object exists...")
        try:
            client.stat_object(bucket_name, object_name)
            logger.info("Object found")
        except S3Error:
            logger.error("Object not found")
            return False

        # Download
        download_file = "/tmp/minio_test_download.txt"
        logger.info(f"Downloading object to {download_file}...")
        client.fget_object(bucket_name, object_name, download_file)
        logger.info("Download successful")

        # Verify content
        with open(download_file, "r") as f:
            downloaded_content = f.read()

        if downloaded_content == test_content:
            logger.info("Content verified (matches original)")
        else:
            logger.error("Content mismatch!")
            return False

        # Clean up
        client.remove_object(bucket_name, object_name)
        logger.info("Test object deleted")

        logger.info("Upload/Download test PASSED!")
        return True

    except S3Error as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = create_buckets()

    if success:
        test_success = test_upload_download()

        if test_success:
            logger.info("=" * 60)
            logger.info("MinIO Setup Complete and Verified!")
            logger.info("=" * 60)
            logger.info("Next steps:")
            logger.info("  1. Access MinIO console: http://localhost:9201")
            logger.info("  2. Create PostgreSQL schema")
            logger.info("  3. Implement backend API endpoints")
            exit(0)
        else:
            logger.error("Upload/Download test failed")
            exit(1)
    else:
        logger.error("Bucket creation failed")
        exit(1)
