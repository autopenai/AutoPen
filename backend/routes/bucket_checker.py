from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
import uuid

router = APIRouter(prefix="/bucket-checker", tags=["Bucket Checker"])

class BucketCheckRequest(BaseModel):
    url: HttpUrl
    check_aws: bool = True
    check_azure: bool = True
    check_gcp: bool = True
    custom_bucket_names: Optional[List[str]] = None

class BucketCheckResponse(BaseModel):
    test_id: str
    status: str
    findings: List[Dict[str, Any]]
    timestamp: datetime

# Store for active tests
active_bucket_tests: Dict[str, Dict[str, Any]] = {}

@router.post("/check", response_model=BucketCheckResponse)
async def start_bucket_check(request: BucketCheckRequest):
    """
    Start checking for open buckets and vulnerable links.
    """
    test_id = str(uuid.uuid4())
    
    # Initialize test data
    test_data = {
        "test_id": test_id,
        "url": str(request.url),
        "status": "running",
        "findings": [],
        "timestamp": datetime.now()
    }
    
    active_bucket_tests[test_id] = test_data
    
    # Start the check asynchronously
    asyncio.create_task(run_bucket_check(test_id, request))
    
    return BucketCheckResponse(**test_data)

@router.get("/check/{test_id}", response_model=BucketCheckResponse)
async def get_bucket_check_status(test_id: str):
    """
    Get the status and results of a bucket check.
    """
    if test_id not in active_bucket_tests:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return BucketCheckResponse(**active_bucket_tests[test_id])

async def run_bucket_check(test_id: str, request: BucketCheckRequest):
    """
    Run the bucket and link vulnerability check.
    """
    test_data = active_bucket_tests[test_id]
    
    try:
        # Check AWS S3 buckets
        if request.check_aws:
            # Example bucket names to check
            aws_buckets = [
                f"{request.url.host.split('.')[0]}-backup",
                f"{request.url.host.split('.')[0]}-dev",
                f"{request.url.host.split('.')[0]}-prod",
                "company-backup",
                "company-assets"
            ]
            
            for bucket in aws_buckets:
                # Here you would implement actual AWS bucket checking logic
                # For now, we'll simulate findings
                if "backup" in bucket:
                    test_data["findings"].append({
                        "type": "aws_s3",
                        "bucket_name": bucket,
                        "status": "public",
                        "severity": "HIGH",
                        "description": "Public S3 bucket found",
                        "url": f"https://{bucket}.s3.amazonaws.com"
                    })
        
        # Check Azure Blob Storage
        if request.check_azure:
            azure_containers = [
                f"{request.url.host.split('.')[0]}-storage",
                "company-files",
                "backup-container"
            ]
            
            for container in azure_containers:
                # Here you would implement actual Azure container checking logic
                if "backup" in container:
                    test_data["findings"].append({
                        "type": "azure_blob",
                        "container_name": container,
                        "status": "public",
                        "severity": "HIGH",
                        "description": "Public Azure container found"
                    })
        
        # Check GCP Storage
        if request.check_gcp:
            gcp_buckets = [
                f"{request.url.host.split('.')[0]}-storage",
                "company-assets-gcp",
                "backup-gcp"
            ]
            
            for bucket in gcp_buckets:
                # Here you would implement actual GCP bucket checking logic
                if "backup" in bucket:
                    test_data["findings"].append({
                        "type": "gcp_storage",
                        "bucket_name": bucket,
                        "status": "public",
                        "severity": "HIGH",
                        "description": "Public GCP bucket found"
                    })
        
        test_data["status"] = "completed"
        
    except Exception as e:
        test_data["status"] = "failed"
        test_data["findings"].append({
            "error": str(e),
            "severity": "ERROR"
        }) 