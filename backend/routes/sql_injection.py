from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
import uuid

router = APIRouter(prefix="/sql-injection", tags=["SQL Injection"])

class SQLInjectionRequest(BaseModel):
    url: HttpUrl
    target_parameters: Optional[List[str]] = None
    custom_payloads: Optional[List[str]] = None

class SQLInjectionResponse(BaseModel):
    test_id: str
    status: str
    findings: List[Dict[str, Any]]
    timestamp: datetime

# Store for active tests
active_sql_tests: Dict[str, Dict[str, Any]] = {}

@router.post("/test", response_model=SQLInjectionResponse)
async def start_sql_injection_test(request: SQLInjectionRequest):
    """
    Start a SQL injection test on the provided URL.
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
    
    active_sql_tests[test_id] = test_data
    
    # Start the test asynchronously
    asyncio.create_task(run_sql_injection_test(test_id, request))
    
    return SQLInjectionResponse(**test_data)

@router.get("/test/{test_id}", response_model=SQLInjectionResponse)
async def get_sql_test_status(test_id: str):
    """
    Get the status and results of a SQL injection test.
    """
    if test_id not in active_sql_tests:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return SQLInjectionResponse(**active_sql_tests[test_id])

async def run_sql_injection_test(test_id: str, request: SQLInjectionRequest):
    """
    Run the SQL injection test with various payloads.
    """
    test_data = active_sql_tests[test_id]
    
    # Default SQL injection payloads
    default_payloads = [
        "' OR '1'='1",
        "' OR 1=1 --",
        "' UNION SELECT NULL--",
        "admin' --",
        "1' ORDER BY 1--",
        "1' AND '1'='1",
        "1' AND '1'='2"
    ]
    
    payloads = request.custom_payloads or default_payloads
    
    try:
        # Simulate testing each payload
        for payload in payloads:
            # Here you would implement actual SQL injection testing logic
            # For now, we'll simulate findings
            if "' OR '1'='1" in payload:
                test_data["findings"].append({
                    "payload": payload,
                    "vulnerable": True,
                    "severity": "HIGH",
                    "description": "Potential SQL injection vulnerability found",
                    "parameter": "username"  # Example parameter
                })
        
        test_data["status"] = "completed"
        
    except Exception as e:
        test_data["status"] = "failed"
        test_data["findings"].append({
            "error": str(e),
            "severity": "ERROR"
        }) 