import asyncio
import base64
import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup


class ContentFormat(Enum):
    HTML = "html"
    TEXT = "text"
    DOM = "dom"
    JSON = "json"


class WaitCondition(Enum):
    LOAD = "load"
    NETWORK_IDLE = "networkidle"
    DOM_CONTENT_LOADED = "domcontentloaded"


@dataclass
class SessionConfig:
    headless: bool = True
    timeout: int = 30000
    viewport: Dict[str, int] = None
    user_agent: str = None
    extra_headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.viewport is None:
            self.viewport = {"width": 1920, "height": 1080}
        if self.extra_headers is None:
            self.extra_headers = {}


class WebSession:
    """
    A comprehensive web interaction session with fluent API design.
    
    Usage:
        session = WebSession("https://example.com")
        await session.start()
        content = await session.get_content(format=ContentFormat.TEXT)
        await session.close()
        
    Or using context manager:
        async with WebSession("https://example.com") as session:
            await session.fill_input("input[name='email']", "user@example.com")
            await session.click("button[type='submit']")
    """
    
    def __init__(self, url: str, config: SessionConfig = None):
        self.url = url
        self.config = config or SessionConfig()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._session_data = {}
        
    async def start(self) -> "WebSession":
        """Initialize the browser session and navigate to the URL."""
        self.playwright = await async_playwright().start()
        
        # Launch browser
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.headless
        )
        
        # Create context with configuration
        context_options = {
            "viewport": self.config.viewport,
            "extra_http_headers": self.config.extra_headers,
        }
        if self.config.user_agent:
            context_options["user_agent"] = self.config.user_agent
            
        self.context = await self.browser.new_context(**context_options)
        
        # Set default timeout
        self.context.set_default_timeout(self.config.timeout)
        
        # Create page and navigate
        self.page = await self.context.new_page()
        await self.page.goto(self.url)
        
        return self
    
    async def close(self):
        """Clean up browser resources."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # Navigation Methods
    async def navigate(self, url: str, wait_condition: WaitCondition = WaitCondition.LOAD) -> "WebSession":
        """Navigate to a new URL."""
        await self.page.goto(url, wait_until=wait_condition.value)
        return self
    
    async def reload(self, wait_condition: WaitCondition = WaitCondition.LOAD) -> "WebSession":
        """Reload the current page."""
        await self.page.reload(wait_until=wait_condition.value)
        return self
    
    async def back(self) -> "WebSession":
        """Navigate back in browser history."""
        await self.page.go_back()
        return self
    
    async def forward(self) -> "WebSession":
        """Navigate forward in browser history."""
        await self.page.go_forward()
        return self
    
    # Content Retrieval Methods
    async def get_content(self, format: ContentFormat = ContentFormat.HTML) -> Union[str, Dict, BeautifulSoup]:
        """
        Retrieve page content in the specified format.
        
        Args:
            format: The desired output format
            
        Returns:
            Content in the requested format
        """
        print(f"Getting content in format: {format}")
        
        if format == ContentFormat.HTML:
            print("Retrieving HTML content...")
            content = await self.page.content()
            print(f"Retrieved {len(content)} characters of HTML")
            return content
            
        elif format == ContentFormat.TEXT:
            print("Retrieving text content...")
            content = await self.page.text_content("body") or ""
            print(f"Retrieved {len(content)} characters of text")
            return content
            
        elif format == ContentFormat.DOM:
            print("Retrieving DOM content...")
            html = await self.page.content()
            dom = BeautifulSoup(html, 'html.parser')
            print("Successfully parsed HTML into DOM")
            return dom
            
        elif format == ContentFormat.JSON:
            print("Retrieving JSON content...")
            # Try to parse page content as JSON
            content = await self.page.text_content("body") or ""
            try:
                json_content = json.loads(content)
                print("Successfully parsed JSON content")
                return json_content
            except json.JSONDecodeError:
                print("Failed to parse JSON content")
                raise ValueError("Page content is not valid JSON")
    
    async def get_screenshot(self, 
                           selector: str = None, 
                           full_page: bool = False,
                           format: str = "png") -> bytes:
        """
        Take a screenshot of the page or specific element.
        
        Args:
            selector: CSS selector for specific element (optional)
            full_page: Whether to capture the full page
            format: Image format ('png' or 'jpeg')
            
        Returns:
            Screenshot as bytes
        """
        screenshot_options = {"type": format, "full_page": full_page}
        
        if selector:
            element = await self.page.query_selector(selector)
            if element:
                return await element.screenshot(**screenshot_options)
            else:
                raise ValueError(f"Element with selector '{selector}' not found")
        else:
            return await self.page.screenshot(**screenshot_options)
    
    async def get_iframe_content(self, iframe_selector: str, format: ContentFormat = ContentFormat.HTML):
        """Extract content from an iframe."""
        iframe_element = await self.page.query_selector(iframe_selector)
        if not iframe_element:
            raise ValueError(f"Iframe with selector '{iframe_selector}' not found")
        
        iframe = await iframe_element.content_frame()
        if not iframe:
            raise ValueError("Could not access iframe content")
        
        if format == ContentFormat.HTML:
            return await iframe.content()
        elif format == ContentFormat.TEXT:
            return await iframe.text_content("body") or ""
        elif format == ContentFormat.DOM:
            html = await iframe.content()
            return BeautifulSoup(html, 'html.parser')
    
    # Element Selection Methods
    async def find_element(self, selector: str):
        """Find element using CSS selector."""
        return await self.page.query_selector(selector)
    
    async def find_elements(self, selector: str):
        """Find multiple elements using CSS selector."""
        return await self.page.query_selector_all(selector)
    
    async def find_by_xpath(self, xpath: str):
        """Find element using XPath."""
        return await self.page.query_selector(f"xpath={xpath}")
    
    async def find_by_text(self, text: str, exact: bool = False):
        """Find element by text content."""
        selector = f"text={text}" if exact else f"text=*{text}*"
        return await self.page.query_selector(selector)
    
    async def find_by_attribute(self, tag: str, attribute: str, value: str):
        """Find element by attribute value."""
        selector = f"{tag}[{attribute}='{value}']"
        return await self.page.query_selector(selector)
    
    # Interaction Methods
    async def click(self, selector: str, timeout: int = None) -> "WebSession":
        """Click an element."""
        options = {}
        if timeout:
            options["timeout"] = timeout
        await self.page.click(selector, **options)
        return self
    
    async def fill_input(self, selector: str, value: str) -> "WebSession":
        """Fill a text input field."""
        await self.page.fill(selector, value)
        return self
    
    async def select_dropdown(self, selector: str, value: str = None, label: str = None) -> "WebSession":
        """Select option from dropdown."""
        if value:
            await self.page.select_option(selector, value=value)
        elif label:
            await self.page.select_option(selector, label=label)
        else:
            raise ValueError("Either value or label must be provided")
        return self
    
    async def check_checkbox(self, selector: str, checked: bool = True) -> "WebSession":
        """Check or uncheck a checkbox."""
        await self.page.set_checked(selector, checked)
        return self
    
    async def select_radio(self, selector: str) -> "WebSession":
        """Select a radio button."""
        await self.page.check(selector)
        return self
    
    async def submit_form(self, form_selector: str = "form") -> "WebSession":
        """Submit a form."""
        await self.page.click(f"{form_selector} input[type='submit'], {form_selector} button[type='submit']")
        return self
    
    async def upload_file(self, selector: str, file_path: str) -> "WebSession":
        """Upload a file to a file input."""
        await self.page.set_input_files(selector, file_path)
        return self
    
    # Wait Methods
    async def wait_for_element(self, selector: str, timeout: int = None) -> "WebSession":
        """Wait for an element to appear."""
        options = {"state": "visible"}
        if timeout:
            options["timeout"] = timeout
        await self.page.wait_for_selector(selector, **options)
        return self
    
    async def wait_for_text(self, text: str, timeout: int = None) -> "WebSession":
        """Wait for text to appear on the page."""
        options = {}
        if timeout:
            options["timeout"] = timeout
        await self.page.wait_for_function(
            f"document.body.textContent.includes('{text}')",
            **options
        )
        return self
    
    async def wait_for_load(self, condition: WaitCondition = WaitCondition.LOAD) -> "WebSession":
        """Wait for page load with specified condition."""
        await self.page.wait_for_load_state(condition.value)
        return self
    
    async def wait_for_network_idle(self, timeout: int = None) -> "WebSession":
        """Wait for network to be idle."""
        options = {}
        if timeout:
            options["timeout"] = timeout
        await self.page.wait_for_load_state("networkidle", **options)
        return self
    
    async def wait_for_url_change(self, expected_url: str = None, timeout: int = None) -> "WebSession":
        """Wait for URL to change."""
        options = {}
        if timeout:
            options["timeout"] = timeout
        
        if expected_url:
            await self.page.wait_for_url(expected_url, **options)
        else:
            current_url = self.page.url
            await self.page.wait_for_function(
                f"window.location.href !== '{current_url}'",
                **options
            )
        return self
    
    # Utility Methods
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript on the page."""
        # If the script starts with 'return', wrap it in a function
        if script.strip().startswith('return'):
            script = f"() => {{ {script} }}"
        return await self.page.evaluate(script)
    
    async def scroll_to(self, selector: str = None, x: int = 0, y: int = 0) -> "WebSession":
        """Scroll to element or coordinates."""
        if selector:
            await self.page.query_selector(selector).scroll_into_view_if_needed()
        else:
            await self.page.evaluate(f"window.scrollTo({x}, {y})")
        return self
    
    async def hover(self, selector: str) -> "WebSession":
        """Hover over an element."""
        await self.page.hover(selector)
        return self
    
    async def get_attribute(self, selector: str, attribute: str) -> str:
        """Get attribute value from an element."""
        return await self.page.get_attribute(selector, attribute)
    
    async def get_text(self, selector: str) -> str:
        """Get text content from an element."""
        return await self.page.text_content(selector) or ""
    
    # Session State Management
    def set_session_data(self, key: str, value: Any):
        """Store data in session state."""
        self._session_data[key] = value
    
    def get_session_data(self, key: str, default: Any = None) -> Any:
        """Retrieve data from session state."""
        return self._session_data.get(key, default)
    
    async def save_cookies(self, file_path: str):
        """Save current cookies to file."""
        cookies = await self.context.cookies()
        with open(file_path, 'w') as f:
            json.dump(cookies, f)
    
    async def load_cookies(self, file_path: str):
        """Load cookies from file."""
        with open(file_path, 'r') as f:
            cookies = json.load(f)
        await self.context.add_cookies(cookies)


# Convenience function for quick operations
async def quick_session(url: str, operations, config: SessionConfig = None):
    """
    Execute operations in a temporary session.
    
    Args:
        url: Target URL
        operations: Async function that takes a WebSession as parameter
        config: Optional session configuration
        
    Example:
        async def my_operations(session):
            await session.fill_input("input[name='search']", "python")
            await session.click("button[type='submit']")
            return await session.get_content(format=ContentFormat.TEXT)
        
        result = await quick_session("https://example.com", my_operations)
    """
    async with WebSession(url, config) as session:
        return await operations(session)
