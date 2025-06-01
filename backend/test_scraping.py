#!/usr/bin/env python3
"""
Basic test script for the playwright interface scraping functionality.

Prerequisites:
    pip install playwright beautifulsoup4
    playwright install chromium

Usage:
    python test_scraping.py
"""

import asyncio
import sys
from pathlib import Path

# Add the backend/bot directory to the path so we can import the playwright interface
sys.path.append(str(Path(__file__).parent / "backend" / "bot"))

from bot.playwright_interface import WebSession, ContentFormat, SessionConfig


async def test_basic_scraping():
    """Test basic scraping functionality on localhost:5000"""
    
    url = "http://localhost:5000"
    
    print(f"🚀 Testing scraping on {url}")
    
    # Create session config (you can modify these settings)
    config = SessionConfig(
        headless=True,  # Set to False if you want to see the browser
        timeout=10000,  # 10 seconds timeout
    )
    
    try:
        # Test using context manager (recommended approach)
        async with WebSession(url, config) as session:
            print("✅ Browser session started successfully")
            
            # Test 1: Get HTML content
            print("\n📄 Test 1: Getting HTML content...")
            html_content = await session.get_content(format=ContentFormat.HTML)
            print(f"HTML length: {len(html_content)} characters")
            print(f"First 200 characters: {html_content[:200]}...")
            
            # Test 2: Get text content
            print("\n📝 Test 2: Getting text content...")
            text_content = await session.get_content(format=ContentFormat.TEXT)
            print(f"Text length: {len(text_content)} characters")
            print(f"Text content: {text_content}")
            
            # Test 3: Get page title
            print("\n🏷️  Test 3: Getting page title...")
            title = await session.execute_script("return document.title")
            print(f"Page title: {title}")
            
            # Test 4: Get current URL
            print("\n🔗 Test 4: Getting current URL...")
            current_url = session.page.url
            print(f"Current URL: {current_url}")
            
            # Test 5: Try to find some common elements
            print("\n🔍 Test 5: Looking for common elements...")
            
            # Look for forms
            forms = await session.find_elements("form")
            print(f"Found {len(forms)} form(s)")
            
            # Look for inputs
            inputs = await session.find_elements("input")
            print(f"Found {len(inputs)} input(s)")
            
            # Look for links
            links = await session.find_elements("a")
            print(f"Found {len(links)} link(s)")
            
            # Test 6: Test DOM content format
            print("\n🌐 Test 6: Getting DOM content...")
            dom_content = await session.get_content(format=ContentFormat.DOM)
            print(f"DOM type: {type(dom_content)}")
            if hasattr(dom_content, 'title'):
                print(f"DOM title: {dom_content.title.string if dom_content.title else 'No title'}")
            
            print("\n✅ All scraping tests completed successfully!")
            
    except Exception as e:
        print(f"❌ Error during scraping test: {e}")
        print(f"Make sure you have a server running on {url}")
        return False
    
    return True


async def test_simple_server_check():
    """Test if we can even connect to the server"""
    
    url = "http://localhost:5000"
    
    print(f"🔍 Testing connection to {url}")
    
    try:
        config = SessionConfig(headless=True, timeout=5000)
        session = WebSession(url, config)
        await session.start()
        
        print("✅ Successfully connected to the server")
        
        # Just get basic page info (fixed the JavaScript execution)
        title = await session.execute_script("return document.title || 'No title'")
        current_url = session.page.url
        
        print(f"Page title: {title}")
        print(f"Final URL: {current_url}")
        
        await session.close()
        return True
        
    except Exception as e:
        print(f"❌ Cannot connect to {url}: {e}")
        print("Make sure you have a web server running on localhost:5000")
        return False


def main():
    """Main function to run the tests"""
    
    print("🧪 Playwright Interface Scraping Test")
    print("=" * 50)
    
    # First, test simple connection
    print("\n📡 Step 1: Testing basic connection...")
    if not asyncio.run(test_simple_server_check()):
        print("\n💡 To test this script, you need a web server running on localhost:5000")
        print("You can start a simple server with:")
        print("  python -m http.server 5000")
        print("Or modify the URL in this script to test a different server.")
        return
    
    # Then run comprehensive tests
    print("\n🔬 Step 2: Running comprehensive scraping tests...")
    success = asyncio.run(test_basic_scraping())
    
    if success:
        print("\n🎉 All tests passed! Your playwright interface is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main() 