from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl, Field
import asyncio
import json
from typing import Optional, Dict, Any, AsyncGenerator, List
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


class PentestStatusResponse(BaseModel):
    test_id: str
    status: TestStatus
    progress_percentage: int
    current_phase: str
    total_events: int
    events: List[Dict[str, Any]]
    vulnerabilities_found: int
    results: Dict[str, Any]


class PentestEvent(BaseModel):
    event_type: EventType
    timestamp: datetime
    message: str
    details: Optional[Dict[str, Any]] = None


class PentestData(BaseModel):
    test_id: str
    url: str
    status: TestStatus
    started_at: datetime
    progress_percentage: int = 0
    current_phase: str = "Initializing"
    vulnerabilities_found: int = 0
    results: Dict[str, Any] = Field(default_factory=dict)
    events: List[PentestEvent] = Field(default_factory=list)

    def add_event(
        self,
        event_type: EventType,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Add an event to this test"""
        event = PentestEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            message=message,
            details=details,
        )
        self.events.append(event)


# Storage for active tests
active_tests: Dict[str, PentestData] = {}


@app.get("/")
async def root():
    return {
        "message": "URL Pentest API",
        "version": "1.0.0",
        "description": "Comprehensive automated penetration testing for web endpoints",
    }


@app.post("/tests", response_model=PentestStartResponse)
async def start_pentest(request: PentestRequest):
    """
    Start a comprehensive penetration test on the provided URL.
    Returns immediately with a test ID to track progress.
    """
    test_id = str(uuid.uuid4())

    # Create test data structure
    test_data = PentestData(
        test_id=test_id,
        url=str(request.url),
        status=TestStatus.PENDING,
        started_at=datetime.now(),
    )

    active_tests[test_id] = test_data

    # Start the pentest asynchronously (don't await)
    asyncio.create_task(run_pentest(test_id, str(request.url)))

    return PentestStartResponse(
        test_id=test_id, status=TestStatus.PENDING, url=str(request.url)
    )


@app.get("/tests/{test_id}", response_model=PentestStatusResponse)
async def get_test_status(test_id: str):
    """
    Get the current status, progress, results, and event history of a pentest.
    """
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    test_data = active_tests[test_id]

    return PentestStatusResponse(
        test_id=test_id,
        status=test_data.status,
        progress_percentage=test_data.progress_percentage,
        current_phase=test_data.current_phase,
        total_events=len(test_data.events),
        events=[
            {
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "message": event.message,
                "details": event.details,
            }
            for event in test_data.events
        ],
        vulnerabilities_found=test_data.vulnerabilities_found,
        results=test_data.results,
    )


@app.get("/tests")
async def list_tests(status: Optional[TestStatus] = None):
    """
    List all tests, optionally filtered by status.
    """
    tests = list(active_tests.values())

    if status:
        tests = [test for test in tests if test.status == status]

    return [
        {
            "test_id": test.test_id,
            "url": test.url,
            "status": test.status,
            "progress_percentage": test.progress_percentage,
        }
        for test in sorted(tests, key=lambda x: x.started_at, reverse=True)
    ]


@app.delete("/tests/{test_id}")
async def cancel_test(test_id: str):
    """
    Cancel a running pentest.
    """
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    test_data = active_tests[test_id]

    if test_data.status in [TestStatus.COMPLETED, TestStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed test")

    # Mark as cancelled
    test_data.status = TestStatus.FAILED
    test_data.current_phase = "Cancelled"
    test_data.add_event(EventType.ERROR, "Test cancelled by user")

    return {"message": f"Test {test_id} cancelled successfully"}


@app.get("/tests/{test_id}/events")
async def stream_test_events(test_id: str):
    """
    Server-Sent Events endpoint to stream real-time pentest events.
    """
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        # Send initial connection event
        yield f"data: {json.dumps({'event': 'connected', 'test_id': test_id})}\n\n"

        last_event_index = 0

        while True:
            # Check if test is still active or completed
            test_data = active_tests.get(test_id)
            if not test_data:
                yield f"data: {json.dumps({'event': 'error', 'message': 'Test not found'})}\n\n"
                break

            # Send any new events
            current_events = test_data.events
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
            if test_data.status in [TestStatus.COMPLETED, TestStatus.FAILED]:
                yield f"data: {json.dumps({'event': 'test_completed', 'status': test_data.status})}\n\n"
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
    """
    test_data = active_tests[test_id]

    try:
        # Update status to running
        test_data.status = TestStatus.RUNNING
        test_data.add_event(EventType.INFO, "Pentest started", {"url": url})

        # Simulate pentest phases with events
        phases = [
            ("Reconnaissance", 15),
            ("Port Scanning", 30),
            ("Vulnerability Scanning", 50),
            ("Web App Testing", 75),
            ("Report Generation", 100),
        ]

        for phase_name, progress in phases:
            test_data.current_phase = phase_name
            test_data.progress_percentage = progress

            test_data.add_event(EventType.INFO, f"Starting {phase_name}")

            # Simulate different types of events during web app testing
            if phase_name == "Web App Testing":
                await simulate_web_testing(test_data)
            else:
                # Simulate other scanning activities
                await simulate_scanning_phase(test_data, phase_name)

            # Check if test was cancelled
            if test_data.status == TestStatus.FAILED:
                test_data.add_event(EventType.ERROR, "Test was cancelled")
                return

        # Mark as completed
        test_data.status = TestStatus.COMPLETED
        test_data.progress_percentage = 100
        test_data.current_phase = "Completed"

        # Add simplified results
        test_data.vulnerabilities_found = 3
        test_data.results = {
            "high_risk": 1,
            "medium_risk": 2,
            "findings": ["SQL injection", "XSS vulnerability", "Weak SSL config"],
        }

        test_data.add_event(
            EventType.INFO,
            "Pentest completed",
            {"vulnerabilities_found": test_data.vulnerabilities_found},
        )

    except Exception as e:
        # Handle errors
        test_data.status = TestStatus.FAILED
        test_data.current_phase = "Failed"
        test_data.vulnerabilities_found = 0
        test_data.results = {"error": str(e)}
        test_data.add_event(EventType.ERROR, f"Pentest failed: {str(e)}")


async def simulate_web_testing(test_data: PentestData):
    """Simulate web application testing with browser automation events"""

    # Simulate loading the page
    test_data.add_event(
        EventType.LOAD, f"Loading page: {test_data.url}", {"url": test_data.url}
    )
    await asyncio.sleep(0.5)

    # Simulate finding and testing forms
    test_data.add_event(EventType.INFO, "Scanning for forms and input fields")
    await asyncio.sleep(0.3)

    # Simulate input field testing
    test_inputs = [
        ("username", "admin"),
        ("password", "' OR 1=1 --"),
        ("search", "<script>alert('xss')</script>"),
        ("email", "test@test.com"),
    ]

    for field_name, test_value in test_inputs:
        test_data.add_event(
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
        test_data.add_event(
            EventType.CLICK, f"Clicking element: {button}", {"element": button}
        )
        await asyncio.sleep(0.3)

    # Simulate finding vulnerabilities
    test_data.add_event(
        EventType.VULNERABILITY,
        "Potential SQL injection found",
        {"severity": "HIGH", "location": "/login", "parameter": "username"},
    )

    test_data.add_event(
        EventType.VULNERABILITY,
        "Cross-site scripting (XSS) vulnerability detected",
        {"severity": "MEDIUM", "location": "/search", "parameter": "q"},
    )


async def simulate_scanning_phase(test_data: PentestData, phase_name: str):
    """Simulate other scanning phases"""

    if phase_name == "Port Scanning":
        ports = [80, 443, 22, 21, 3306, 5432]
        for port in ports:
            status = "open" if port in [80, 443] else "closed"
            test_data.add_event(
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
            test_data.add_event(
                EventType.VULNERABILITY,
                f"Checking {cve}: {desc}",
                {"cve": cve, "severity": severity, "status": "not_vulnerable"},
            )
            await asyncio.sleep(0.4)

    else:
        # Generic scanning events
        await asyncio.sleep(1)
        test_data.add_event(
            EventType.SCAN, f"Completed {phase_name} scan", {"phase": phase_name}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
