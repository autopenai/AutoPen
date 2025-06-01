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
            
            parts = query.split(',', 1)
            if len(parts) != 2:
                return "Error: Input should be 'selector,text'"
            selector, text = parts[0].strip(), parts[1].strip()
            
            if not current_session:
                return "Error: Session not initialized"
            
            await current_session.fill_input(selector, text)
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
            
            selector = query.strip()
            if not current_session:
                return "Error: Session not initialized"
            
            await current_session.click(selector)
            # Wait a moment for any page changes
            await asyncio.sleep(1)
            return f"Successfully clicked element with selector '{selector}'"
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
        # Initialize Playwright session using context manager (like your working test)
        print("🌐 Initializing browser session...")
        config = SessionConfig(headless=True, timeout=10000)
        
        async with WebSession(target_url, config) as session:
            # Store session globally for tools to access
            global current_session
            current_session = session
            
            print("✅ Browser session started successfully")
            
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
            
            # Run the agent asynchronously
            result = await agent.ainvoke({"input": initial_prompt})
            
            print("\n" + "="*60)
            print("🏁 FINAL ASSESSMENT RESULT:")
            print("="*60)
            print(result.get("output", "No output available"))
            print("="*60)
        
        # Session automatically closed by context manager
        print("🧹 Browser session closed")
        
    except Exception as e:
        print(f"❌ Error during assessment: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    # Run the async main function
    asyncio.run(main()) 