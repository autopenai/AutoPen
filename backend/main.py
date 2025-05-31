from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
import asyncio
import json
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from enum import Enum
import uuid

app = FastAPI(title="Pentest API", version="1.0.0")


class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(str, Enum):
    LOAD = "load"
    CLICK = "click"
    INPUT = "input"
    SCAN = "scan"
    VULNERABILITY = "vulnerability"
    ERROR = "error"
    INFO = "info"


class PentestRequest(BaseModel):
    url: HttpUrl


class PentestStartResponse(BaseModel):
    test_id: str
    status: TestStatus
    url: str
    started_at: datetime


class PentestStatusResponse(BaseModel):
    test_id: str
    status: TestStatus
    url: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress_percentage: int
    current_phase: str
    estimated_time_remaining_minutes: Optional[int] = None


class PentestResultsResponse(BaseModel):
    test_id: str
    url: str
    status: TestStatus
    started_at: datetime
    completed_at: Optional[datetime]
    total_duration_minutes: Optional[float] = None
    summary: Optional[Dict[str, Any]] = None
    detailed_results: Optional[Dict[str, Any]] = None
    vulnerabilities_found: Optional[int] = None
    risk_level: Optional[str] = None


class PentestEvent(BaseModel):
    event_type: EventType
    timestamp: datetime
    message: str
    details: Optional[Dict[str, Any]] = None


# In-memory storage (replace with database in production)
active_tests: Dict[str, Dict[str, Any]] = {}
test_events: Dict[str, list[PentestEvent]] = {}  # Store events per test


@app.get("/")
async def root():
    return {
        "message": "URL Pentest API",
        "version": "1.0.0",
        "description": "Comprehensive automated penetration testing for web endpoints",
    }


@app.post("/test", response_model=PentestStartResponse)
async def start_pentest(request: PentestRequest):
    """
    Start a comprehensive penetration test on the provided URL.

    This will run a full automated pentest including:
    - Port scanning
    - Vulnerability scanning
    - Web application security testing
    - SSL/TLS analysis
    - Directory enumeration
    - And more...

    Returns immediately with a test ID to track progress.
    """
    test_id = str(uuid.uuid4())
    started_at = datetime.now()

    # Store test metadata
    active_tests[test_id] = {
        "test_id": test_id,
        "url": str(request.url),
        "callback_url": str(request.callback_url) if request.callback_url else None,
        "status": TestStatus.PENDING,
        "started_at": started_at,
        "progress_percentage": 0,
        "current_phase": "Initializing",
        "estimated_time_remaining_minutes": 45,
    }

    # Start the pentest asynchronously (don't await)
    asyncio.create_task(run_pentest(test_id, str(request.url)))

    return PentestStartResponse(
        test_id=test_id,
        status=TestStatus.PENDING,
        url=str(request.url),
        started_at=started_at,
        estimated_duration_minutes=45,
    )


@app.get("/test/{test_id}/status", response_model=PentestStatusResponse)
async def get_test_status(test_id: str):
    """
    Get the current status and progress of a running pentest.
    """
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    test_data = active_tests[test_id]

    return PentestStatusResponse(
        test_id=test_id,
        status=test_data["status"],
        url=test_data["url"],
        started_at=test_data["started_at"],
        completed_at=test_data.get("completed_at"),
        progress_percentage=test_data["progress_percentage"],
        current_phase=test_data["current_phase"],
        estimated_time_remaining_minutes=test_data.get(
            "estimated_time_remaining_minutes"
        ),
    )


@app.get("/test/{test_id}/results", response_model=PentestResultsResponse)
async def get_test_results(test_id: str):
    """
    Get the detailed results of a completed pentest.
    """
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    test_data = active_tests[test_id]

    if test_data["status"] not in [TestStatus.COMPLETED, TestStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Test is still {test_data['status']}. Results not available yet.",
        )

    return PentestResultsResponse(
        test_id=test_id,
        url=test_data["url"],
        status=test_data["status"],
        started_at=test_data["started_at"],
        completed_at=test_data.get("completed_at"),
        total_duration_minutes=test_data.get("total_duration_minutes"),
        summary=test_data.get("summary"),
        detailed_results=test_data.get("detailed_results"),
        vulnerabilities_found=test_data.get("vulnerabilities_found"),
        risk_level=test_data.get("risk_level"),
    )


@app.get("/tests")
async def list_tests(status: Optional[TestStatus] = None, limit: int = 50):
    """
    List all tests, optionally filtered by status.
    """
    tests = list(active_tests.values())

    if status:
        tests = [test for test in tests if test["status"] == status]

    tests = sorted(tests, key=lambda x: x["started_at"], reverse=True)[:limit]

    return {
        "total": len(tests),
        "tests": [
            {
                "test_id": test["test_id"],
                "url": test["url"],
                "status": test["status"],
                "started_at": test["started_at"],
                "progress_percentage": test["progress_percentage"],
            }
            for test in tests
        ],
    }


@app.delete("/test/{test_id}")
async def cancel_test(test_id: str):
    """
    Cancel a running pentest.
    """
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    test_data = active_tests[test_id]

    if test_data["status"] in [TestStatus.COMPLETED, TestStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed test")

    # Mark as cancelled (you'd implement actual cancellation logic)
    test_data["status"] = TestStatus.FAILED
    test_data["completed_at"] = datetime.now()
    test_data["current_phase"] = "Cancelled"

    return {"message": f"Test {test_id} cancelled successfully"}


@app.get("/test/{test_id}/events")
async def stream_test_events(test_id: str):
    """
    Server-Sent Events endpoint to stream real-time pentest events.
    """
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        # Send initial connection event
        yield f"data: {json.dumps({'event': 'connected', 'test_id': test_id})}\n\n"

        # Initialize events list if not exists
        if test_id not in test_events:
            test_events[test_id] = []

        last_event_index = 0

        while True:
            # Check if test is still active or completed
            test_data = active_tests.get(test_id)
            if not test_data:
                yield f"data: {json.dumps({'event': 'error', 'message': 'Test not found'})}\n\n"
                break

            # Send any new events
            current_events = test_events.get(test_id, [])
            if len(current_events) > last_event_index:
                for event in current_events[last_event_index:]:
                    event_data = {
                        "event": event.event_type,
                        "timestamp": event.timestamp.isoformat(),
                        "message": event.message,
                        "details": event.details,
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"

                last_event_index = len(current_events)

            # If test is completed or failed, send final event and close
            if test_data["status"] in [TestStatus.COMPLETED, TestStatus.FAILED]:
                yield f"data: {json.dumps({'event': 'test_completed', 'status': test_data['status']})}\n\n"
                break

            # Wait before checking for more events
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


async def run_pentest(test_id: str, url: str):
    """
    Placeholder for the actual pentest implementation.
    This will be replaced with your comprehensive testing logic.
    """
    test_data = active_tests[test_id]

    # Initialize events list for this test
    test_events[test_id] = []

    def add_event(
        event_type: EventType, message: str, details: Optional[Dict[str, Any]] = None
    ):
        """Helper function to add events"""
        event = PentestEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            message=message,
            details=details,
        )
        test_events[test_id].append(event)

    try:
        # Update status to running
        test_data["status"] = TestStatus.RUNNING
        add_event(EventType.INFO, "Pentest started", {"url": url})

        # Simulate pentest phases with events
        phases = [
            ("Reconnaissance", 10, "Gathering initial information about the target"),
            ("Port Scanning", 20, "Scanning for open ports and services"),
            ("Vulnerability Scanning", 40, "Running automated vulnerability scans"),
            ("Web App Testing", 60, "Testing web application security"),
            ("SSL/TLS Analysis", 75, "Analyzing SSL/TLS configuration"),
            ("Directory Enumeration", 85, "Enumerating directories and files"),
            (
                "Exploitation Attempts",
                95,
                "Attempting to exploit discovered vulnerabilities",
            ),
            ("Report Generation", 100, "Generating comprehensive security report"),
        ]

        for phase_name, progress, description in phases:
            test_data["current_phase"] = phase_name
            test_data["progress_percentage"] = progress
            test_data["estimated_time_remaining_minutes"] = max(
                0, 45 - (progress * 0.45)
            )

            add_event(
                EventType.INFO, f"Starting {phase_name}", {"description": description}
            )

            # Simulate different types of events during web app testing
            if phase_name == "Web App Testing":
                await simulate_web_testing(test_id, url, add_event)
            else:
                # Simulate other scanning activities
                await simulate_scanning_phase(test_id, phase_name, add_event)

            # Check if test was cancelled
            if test_data["status"] == TestStatus.FAILED:
                add_event(EventType.ERROR, "Test was cancelled")
                return

        # Mark as completed
        test_data["status"] = TestStatus.COMPLETED
        test_data["completed_at"] = datetime.now()
        test_data["progress_percentage"] = 100
        test_data["current_phase"] = "Completed"

        # Calculate duration
        duration = (
            test_data["completed_at"] - test_data["started_at"]
        ).total_seconds() / 60
        test_data["total_duration_minutes"] = round(duration, 2)

        # Add placeholder results
        test_data["summary"] = {
            "total_tests_run": 150,
            "vulnerabilities_found": 3,
            "critical_issues": 0,
            "high_risk_issues": 1,
            "medium_risk_issues": 2,
            "low_risk_issues": 0,
        }
        test_data["vulnerabilities_found"] = 3
        test_data["risk_level"] = "MEDIUM"
        test_data["detailed_results"] = {
            "scan_results": "Detailed results would go here...",
            "recommendations": "Security recommendations would go here...",
        }

        add_event(
            EventType.INFO,
            "Pentest completed successfully",
            {
                "vulnerabilities_found": test_data["vulnerabilities_found"],
                "risk_level": test_data["risk_level"],
            },
        )

    except Exception as e:
        # Handle errors
        test_data["status"] = TestStatus.FAILED
        test_data["completed_at"] = datetime.now()
        test_data["current_phase"] = f"Failed: {str(e)}"
        test_data["error"] = str(e)
        add_event(EventType.ERROR, f"Pentest failed: {str(e)}")


async def simulate_web_testing(test_id: str, url: str, add_event):
    """Simulate web application testing with browser automation events"""

    # Simulate loading the page
    add_event(EventType.LOAD, f"Loading page: {url}", {"url": url})
    await asyncio.sleep(0.5)

    # Simulate finding and testing forms
    add_event(EventType.INFO, "Scanning for forms and input fields")
    await asyncio.sleep(0.3)

    # Simulate input field testing
    test_inputs = [
        ("username", "admin"),
        ("password", "' OR 1=1 --"),
        ("search", "<script>alert('xss')</script>"),
        ("email", "test@test.com"),
    ]

    for field_name, test_value in test_inputs:
        add_event(
            EventType.INPUT,
            f"Testing input field: {field_name}",
            {
                "field": field_name,
                "test_value": test_value[:20] + "..."
                if len(test_value) > 20
                else test_value,
            },
        )
        await asyncio.sleep(0.2)

    # Simulate clicking buttons and links
    test_clicks = ["Login", "Submit", "Search", "Contact", "Admin"]
    for button in test_clicks:
        add_event(EventType.CLICK, f"Clicking element: {button}", {"element": button})
        await asyncio.sleep(0.3)

    # Simulate finding vulnerabilities
    add_event(
        EventType.VULNERABILITY,
        "Potential SQL injection found",
        {"severity": "HIGH", "location": "/login", "parameter": "username"},
    )

    add_event(
        EventType.VULNERABILITY,
        "Cross-site scripting (XSS) vulnerability detected",
        {"severity": "MEDIUM", "location": "/search", "parameter": "q"},
    )


async def simulate_scanning_phase(test_id: str, phase_name: str, add_event):
    """Simulate other scanning phases"""

    if phase_name == "Port Scanning":
        ports = [80, 443, 22, 21, 3306, 5432]
        for port in ports:
            status = "open" if port in [80, 443] else "closed"
            add_event(
                EventType.SCAN,
                f"Port {port}: {status}",
                {
                    "port": port,
                    "status": status,
                    "service": "http"
                    if port == 80
                    else "https"
                    if port == 443
                    else "unknown",
                },
            )
            await asyncio.sleep(0.1)

    elif phase_name == "Vulnerability Scanning":
        vulnerabilities = [
            ("CVE-2021-44228", "Log4j Remote Code Execution", "CRITICAL"),
            ("CVE-2021-34527", "Windows Print Spooler", "HIGH"),
            ("SSL-001", "Weak SSL Configuration", "MEDIUM"),
        ]

        for cve, desc, severity in vulnerabilities:
            add_event(
                EventType.VULNERABILITY,
                f"Checking {cve}: {desc}",
                {"cve": cve, "severity": severity, "status": "not_vulnerable"},
            )
            await asyncio.sleep(0.4)

    else:
        # Generic scanning events
        await asyncio.sleep(1)
        add_event(EventType.SCAN, f"Completed {phase_name} scan", {"phase": phase_name})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
