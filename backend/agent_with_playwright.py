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


class PlaywrightWrapper:
    """Wrapper class to provide sync-like interface to async WebSession"""
    
    def __init__(self):
        self.session: Optional[WebSession] = None
        self.loop = None
    
    async def initialize(self, url: str, headless: bool = True):
        """Initialize the Playwright session"""
        config = SessionConfig(headless=headless, timeout=5000)  # 5 second timeout for local testing
        self.session = WebSession(url, config)
        await self.session.start()
        return self.session
    
    def run_async(self, coro):
        """Run async function in a safe way"""
        try:
            # Try to get the current loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No loop running, create a new one
            return asyncio.run(coro)
        else:
            # Loop is running, we need to handle this differently
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=30)  # 30 second timeout
    
    async def input_textbox(self, selector: str, text: str) -> str:
        """Type text into an input field"""
        if not self.session:
            return "Error: Session not initialized"
        try:
            await self.session.fill_input(selector, text)
            return f"Successfully typed '{text}' into element with selector '{selector}'"
        except Exception as e:
            return f"Error typing into textbox: {str(e)}"
    
    async def click_button(self, selector: str) -> str:
        """Click a button or element"""
        if not self.session:
            return "Error: Session not initialized"
        try:
            await self.session.click(selector)
            # Wait a moment for any page changes
            await asyncio.sleep(1)
            return f"Successfully clicked element with selector '{selector}'"
        except Exception as e:
            return f"Error clicking button: {str(e)}"
    
    async def scrape_page(self) -> str:
        print("\n\nScraping page through Playwright")
        """Scrape the current page content"""
        if not self.session:
            print("Error: Session not initialized")
            return "Error: Session not initialized"
        try:
            print("Getting text content...")
            # Get text content for better readability by the LLM with timeout
            try:
                content = await asyncio.wait_for(
                    self.session.get_content(ContentFormat.TEXT), 
                    timeout=8.0
                )
            except asyncio.TimeoutError:
                print("Text content retrieval timed out, trying fallback...")
                content = "Text content retrieval timed out"
            
            print("Getting HTML content...")
            # Also get some HTML structure for form detection with timeout
            try:
                html_content = await asyncio.wait_for(
                    self.session.get_content(ContentFormat.HTML), 
                    timeout=8.0
                )
            except asyncio.TimeoutError:
                print("HTML content retrieval timed out, using minimal HTML...")
                html_content = "<html><body>HTML retrieval timed out</body></html>"
            
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
                    selector = f"#{inp_id}" if inp_id else f"input[name='{inp_name}']"
                    form_info.append(f"  - {inp_type} input: {inp_name} (selector: {selector})")
            
            print("Processing buttons...")
            button_info = []
            for btn in buttons:
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
    
    async def cleanup(self):
        """Clean up the session"""
        if self.session:
            await self.session.close()


# Global wrapper instance
playwright_wrapper = PlaywrightWrapper()


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
        print(f"Inputting text with query: {query}")
        """Execute the tool synchronously by running async code"""
        try:
            if not query or query.lower() in ['none', 'null', '']:
                return "Error: Input required in format 'selector,text'"
            
            parts = query.split(',', 1)
            if len(parts) != 2:
                return "Error: Input should be 'selector,text'"
            selector, text = parts[0].strip(), parts[1].strip()
            
            return playwright_wrapper.run_async(
                playwright_wrapper.input_textbox(selector, text)
            )
        except Exception as e:
            return f"Error: {str(e)}\n{traceback.format_exc()}"


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
        print(f"Clicking button with query: {query}")
        """Execute the tool synchronously"""
        try:
            if not query or query.lower() in ['none', 'null', '']:
                return "Error: CSS selector required"
            
            selector = query.strip()
            return playwright_wrapper.run_async(
                playwright_wrapper.click_button(selector)
            )
        except Exception as e:
            return f"Error: {str(e)}\n{traceback.format_exc()}"


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
        print(f"Scraping page with query: {query}")
        """Execute the tool synchronously"""
        try:
            # Handle None or empty input gracefully
            if query is None:
                query = "scrape"
            
            return playwright_wrapper.run_async(
                playwright_wrapper.scrape_page()
            )
        except Exception as e:
            return f"Error: {str(e)}\n{traceback.format_exc()}"


def create_vulnerability_agent() -> AgentExecutor:
    """Create a LangChain agent with Playwright tools for vulnerability testing"""
    
    # Initialize OpenAI LLM
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create tools
    tools = [
        InputTextBoxTool(),
        ClickButtonTool(),
        ScrapePageTool()
    ]
    
    # Use a custom prompt that handles tool inputs better
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
Final Answer: the final answer to the original input question

IMPORTANT: 
- For scrape_page tool, always use "scrape" as Action Input
- For input_textbox tool, use format "selector,text" as Action Input
- For click_button tool, use the CSS selector as Action Input
- Never use None, null, or empty values as Action Input

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
        max_iterations=15,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )
    
    return agent_executor


async def main():
    """Main function to run the vulnerability testing agent"""
    
    # Get target URL from command line or use default
    target_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080/login"
    
    print(f"🎯 Target URL: {target_url}")
    print("🚀 Starting vulnerability assessment...")
    
    try:
        # Initialize Playwright session
        print("🌐 Initializing browser session...")
        await playwright_wrapper.initialize(target_url, headless=True)
        
        # Create and run the agent
        print("🤖 Creating LangChain agent...")
        agent = create_vulnerability_agent()
        
        # Initial prompt for the agent
        initial_prompt = f"""
        You are a web security expert testing the login page at {target_url} for SQL injection vulnerabilities.
        
        You have access to three tools:
        1. scrape_page: Get current page content and detect forms/inputs (Action Input: "scrape")
        2. input_textbox: Enter text into input fields (Action Input: "selector,text")
        3. click_button: Click buttons or submit forms (Action Input: "selector")
        
        IMPORTANT: Always provide proper Action Input strings - never use None, null, or empty values.
        
        Please follow these steps systematically:
        1. Use scrape_page with Action Input "scrape" to understand the page structure
        2. Identify login form fields (username/password inputs)
        3. Test SQL injection by:
           - Using input_textbox with Action Input "input[name='username'],admin" to enter username
           - Using input_textbox with Action Input "input[name='password'],' OR 1=1--" to enter malicious password  
           - Using click_button with Action Input "input[type='submit']" to submit the form
        4. Use scrape_page with Action Input "scrape" again to check if login was successful
        5. Look for signs of successful login (welcome messages, dashboard, etc.)
        6. Report whether SQL injection vulnerability was detected
        
        Begin your assessment now.
        """
        
        print("🔍 Running vulnerability assessment...")
        result = agent.invoke({"input": initial_prompt})
        
        print("\n" + "="*60)
        print("🏁 FINAL ASSESSMENT RESULT:")
        print("="*60)
        print(result.get("output", "No output available"))
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error during assessment: {str(e)}")
        traceback.print_exc()
    finally:
        # Clean up
        print("🧹 Cleaning up browser session...")
        await playwright_wrapper.cleanup()


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    # Run the async main function
    asyncio.run(main()) 