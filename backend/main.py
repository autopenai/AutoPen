from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
import asyncio
import json
from typing import Optional, Dict, AsyncGenerator, List
from datetime import datetime
from enum import Enum
import uuid

# Import the agent testing function
from agent_with_playwright import run_vulnerability_test
from events import EventType, LoadEventDetails, Vulnerability, GenericEventDetails, EventDetails

app = FastAPI(title="Pentest API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PentestRequest(BaseModel):
    url: HttpUrl


class PentestStartResponse(BaseModel):
    test_id: str
    status: TestStatus
    url: str


class PentestEvent(BaseModel):
    event_type: EventType
    timestamp: datetime
    message: str
    details: Optional[EventDetails] = None


class PentestStatusResponse(BaseModel):
    test_id: str
    status: TestStatus
    progress_percentage: int
    current_phase: str
    events: List[PentestEvent]
    results: List[Vulnerability]


class PentestData(BaseModel):
    test_id: str
    url: str
    status: TestStatus
    started_at: datetime
    progress_percentage: int = 0
    current_phase: str = "Initializing"
    results: List[Vulnerability] = Field(default_factory=list)
    events: List[PentestEvent] = Field(default_factory=list)

    def add_event(
        self,
        event_type: EventType,
        message: str,
        details: Optional[EventDetails] = None,
    ):
        """Add an event to this test"""
        event = PentestEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            message=message,
            details=details,
        )
        self.events.append(event)

    def add_vulnerability(self, vulnerability: Vulnerability):
        """Add a vulnerability to the results"""
        self.results.append(vulnerability)


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
        events=test_data.events,
        results=test_data.results,
    )


@app.get("/tests", response_model=List[PentestStatusResponse])
async def list_tests(status: Optional[TestStatus] = None):
    """
    List all tests, optionally filtered by status.
    """
    tests = list(active_tests.values())

    if status:
        tests = [test for test in tests if test.status == status]

    return [
        PentestStatusResponse(
            test_id=test.test_id,
            status=test.status,
            progress_percentage=test.progress_percentage,
            current_phase=test.current_phase,
            events=test.events,
            results=test.results,
        )
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
                        "details": event.details.dict() if event.details else None,
                    }
                    yield f"data: {json.dumps(event_data, default=str)}\n\n"

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
    Run actual penetration test using LangChain agent with Playwright.
    """
    test_data = active_tests[test_id]

    try:
        # Update status to running
        test_data.status = TestStatus.RUNNING
        test_data.add_event(
            EventType.INFO, "Pentest started", GenericEventDetails(data={"url": url})
        )

        # Phase 1: Reconnaissance
        test_data.current_phase = "Reconnaissance"
        test_data.progress_percentage = 15
        test_data.add_event(EventType.INFO, "Starting reconnaissance phase")

        # Phase 2: Web Application Testing with Real Agent
        test_data.current_phase = "Web Application Testing"
        test_data.progress_percentage = 50
        test_data.add_event(
            EventType.INFO, "Starting web application testing with AI agent"
        )

        test_data.add_event(
            EventType.LOAD,
            f"Loading page: {url}",
            LoadEventDetails(url=url),
        )

        # Run the actual vulnerability test with event callback
        test_results = await run_vulnerability_test(url, test_data.add_event)

        if test_results["success"]:
            agent_output = test_results["agent_output"]
            test_data.add_event(
                EventType.INFO,
                "AI agent completed analysis",
                GenericEventDetails(
                    message=agent_output[:500] + "..."
                    if len(agent_output) > 500
                    else agent_output
                ),
            )

            # Parse JSON vulnerabilities from agent output
            vulnerabilities = []
            try:
                import re

                # Extract JSON array from agent output
                json_match = re.search(r"\[.*?\]", agent_output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    parsed_vulnerabilities = json.loads(json_str)

                    # Validate and process each vulnerability
                    for vuln_data in parsed_vulnerabilities:
                        if isinstance(vuln_data, dict) and all(
                            key in vuln_data
                            for key in ["severity", "type", "title", "description"]
                        ):
                            # Validate severity levels
                            severity = vuln_data["severity"].upper()
                            if severity not in ["HIGH", "MEDIUM", "LOW"]:
                                severity = "MEDIUM"  # Default fallback

                            vulnerabilities.append(
                                {
                                    "severity": severity,
                                    "type": vuln_data["type"],
                                    "title": vuln_data["title"],
                                    "description": vuln_data["description"],
                                }
                            )

                # Fallback: if no JSON found, try legacy detection
                if not vulnerabilities:
                    agent_output_lower = agent_output.lower()

                    if "sql injection" in agent_output_lower and (
                        "successful" in agent_output_lower
                        or "vulnerability" in agent_output_lower
                    ):
                        vulnerabilities.append(
                            {
                                "severity": "HIGH",
                                "type": "SQL Injection",
                                "title": "Authentication Bypass via SQL Injection",
                                "description": "The login form is vulnerable to SQL injection attacks. The agent was able to bypass authentication using malicious SQL payloads.",
                            }
                        )

                    if (
                        "xss" in agent_output_lower
                        or "cross-site scripting" in agent_output_lower
                    ):
                        vulnerabilities.append(
                            {
                                "severity": "MEDIUM",
                                "type": "XSS",
                                "title": "Cross-Site Scripting Vulnerability",
                                "description": "The application is vulnerable to XSS attacks. User input is not properly sanitized before being reflected in the page.",
                            }
                        )

            except json.JSONDecodeError as e:
                test_data.add_event(
                    EventType.ERROR,
                    f"Failed to parse agent JSON output: {str(e)}",
                    GenericEventDetails(
                        message=f"Agent output: {agent_output[:200]}..."
                    ),
                )

                # Emergency fallback - create generic vulnerability if indicators present
                agent_output_lower = agent_output.lower()
                if any(
                    keyword in agent_output_lower
                    for keyword in [
                        "vulnerability",
                        "injection",
                        "xss",
                        "exploit",
                        "successful",
                    ]
                ):
                    vulnerabilities.append(
                        {
                            "severity": "MEDIUM",
                            "type": "Security Vulnerability",
                            "title": "Potential Security Issue Detected",
                            "description": f"The security agent detected potential vulnerabilities: {agent_output[:200]}...",
                        }
                    )

            # Process vulnerabilities and add to results (only if not already added by agent)
            for vuln_data in vulnerabilities:
                # Check if this vulnerability was already added by the agent
                existing_vulns = [
                    v for v in test_data.results if v.title == vuln_data["title"]
                ]
                if not existing_vulns:
                    # Create Vulnerability object
                    vulnerability = Vulnerability(
                        severity=vuln_data["severity"],
                        type=vuln_data["type"],
                        title=vuln_data["title"],
                        description=vuln_data["description"],
                    )

                    # Add to results
                    test_data.add_vulnerability(vulnerability)

                    # Add event (only if not already added by agent)
                    existing_events = [
                        e
                        for e in test_data.events
                        if e.event_type == EventType.VULNERABILITY
                        and vuln_data["title"] in e.message
                    ]
                    if not existing_events:
                        test_data.add_event(
                            EventType.VULNERABILITY,
                            f"Vulnerability detected: {vuln_data['title']}",
                            vulnerability,
                        )

            # Report vulnerability count
            if len(test_data.results) > 0:
                test_data.add_event(
                    EventType.INFO,
                    f"Total vulnerabilities found: {len(test_data.results)}",
                    GenericEventDetails(
                        data={"vulnerability_count": len(test_data.results)}
                    ),
                )
            else:
                test_data.add_event(
                    EventType.INFO,
                    "No vulnerabilities detected",
                    GenericEventDetails(data={"vulnerability_count": 0}),
                )

            # Phase 3: Report Generation
            test_data.current_phase = "Report Generation"
            test_data.progress_percentage = 100
            test_data.add_event(EventType.INFO, "Generating final report")

            # Mark as completed
            test_data.status = TestStatus.COMPLETED
            test_data.progress_percentage = 100
            test_data.current_phase = "Completed"

            test_data.add_event(
                EventType.INFO,
                "Pentest completed",
                GenericEventDetails(
                    data={"vulnerabilities_found": len(test_data.results)}
                ),
            )

        else:
            # Agent test failed
            error_msg = test_results.get("error", "Unknown error")
            test_data.add_event(
                EventType.ERROR,
                f"Agent testing failed: {error_msg}",
                GenericEventDetails(message=error_msg),
            )

    except Exception as e:
        # Handle errors
        test_data.status = TestStatus.FAILED
        test_data.current_phase = "Failed"
        test_data.add_event(
            EventType.ERROR,
            f"Pentest failed: {str(e)}",
            GenericEventDetails(message=str(e)),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
