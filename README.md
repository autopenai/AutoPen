# SQL Injection Testing Agent with LangChain + Playwright

A powerful automated security testing agent that uses LangChain and Playwright to detect SQL injection vulnerabilities in login pages.

## 🔧 Prerequisites

### 1. Install Python packages

**Option A: Using requirements.txt (recommended)**

```bash
pip install -r requirements.txt
```

**Option B: Manual installation**

```bash
pip install langchain langchain-openai playwright beautifulsoup4 flask
```

### 2. Install Playwright browsers

```bash
playwright install
```

### 3. Set up OpenAI API key

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

## 📁 Files Overview

- **`agent_with_playwright.py`** - Main agent script that performs vulnerability testing
- **`playwright_interface.py`** - Playwright wrapper with WebSession class (provided)
- **`test_server.py`** - Vulnerable test server for demonstration
- **`requirements.txt`** - Python package dependencies
- **`README.md`** - This documentation

## 🚀 Quick Start

### Option 1: Test with included vulnerable server

1. **Start the test server:**

   ```bash
   python test_server.py
   ```

   This starts a Flask server at `http://localhost:8080` with an intentionally vulnerable login page.

2. **Run the agent in another terminal:**
   ```bash
   python agent_with_playwright.py http://localhost:8080/login
   ```

### Option 2: Test external website

```bash
python agent_with_playwright.py https://example.com/login
```

## 🤖 How the Agent Works

The agent follows a systematic approach:

1. **🔍 Page Analysis**: Scrapes the target page to identify forms and input fields
2. **🎯 Target Identification**: Locates username and password fields
3. **💉 Injection Attempt**: Enters SQL injection payloads:
   - Username: `admin`
   - Password: `' OR 1=1--`
4. **📤 Form Submission**: Clicks the submit button
5. **✅ Results Analysis**: Checks if authentication was bypassed
6. **📋 Reporting**: Provides detailed findings

## 🛠 Agent Architecture

### LangChain Tools

The agent uses three custom tools:

#### 1. `ScrapePageTool`

- **Purpose**: Extract page content and detect forms
- **Parameters**: None
- **Returns**: Page text content + detected forms and buttons with CSS selectors

#### 2. `InputTextBoxTool`

- **Purpose**: Enter text into form fields
- **Parameters**:
  - `selector`: CSS selector for the input field
  - `text`: Text to enter
- **Returns**: Success/error message

#### 3. `ClickButtonTool`

- **Purpose**: Click buttons or submit forms
- **Parameters**:
  - `selector`: CSS selector for the button
- **Returns**: Success/error message

### Playwright Integration

The agent uses the existing `WebSession` class from `playwright_interface.py`:

- Async/await support for modern web apps
- Configurable browser settings (headless mode, timeouts, etc.)
- Comprehensive element interaction methods
- Screenshot capabilities for debugging

## 📊 Example Output

```
🎯 Target URL: http://localhost:8080/login
🚀 Starting vulnerability assessment...
🌐 Initializing browser session...
🤖 Creating LangChain agent...
🔍 Running vulnerability assessment...

> Entering new AgentExecutor chain...
I need to test this login page for SQL injection vulnerabilities. Let me start by scraping the page to understand its structure.

Action: scrape_page
Action Input: {}

Observation: === PAGE CONTENT ===
Login Page

Username:

Password:

Login

Valid credentials: admin/secret123 or user/password

=== FORMS DETECTED ===
Form 1: 2 inputs
  - text input: username (selector: input[name='username'])
  - password input: password (selector: input[name='password'])

=== BUTTONS DETECTED ===
Button: 'Login' (selector: input[type='submit'])

Now I can see there's a login form with username and password fields. Let me attempt SQL injection by entering "admin" as username and "' OR 1=1--" as password.

Action: input_textbox
Action Input: {"selector": "input[name='username']", "text": "admin"}

Observation: Successfully typed 'admin' into element with selector 'input[name='username']'

Action: input_textbox
Action Input: {"selector": "input[name='password']", "text": "' OR 1=1--"}

Observation: Successfully typed '' OR 1=1--' into element with selector 'input[name='password']'

Now let me submit the form by clicking the login button.

Action: click_button
Action Input: {"selector": "input[type='submit']"}

Observation: Successfully clicked element with selector 'input[type='submit']'

Let me scrape the page again to see if the login was successful and authentication was bypassed.

Action: scrape_page
Action Input: {}

Observation: === PAGE CONTENT ===
Welcome to the Dashboard!

✅ Login successful! You are now authenticated.

Username: admin

This page confirms that authentication was bypassed.

Logout

=== FORMS DETECTED ===

=== BUTTONS DETECTED ===

🚨 VULNERABILITY DETECTED! The SQL injection attack was successful. The page now shows "Welcome to the Dashboard!" and "Login successful! You are now authenticated" which confirms that authentication was bypassed using the SQL injection payload "' OR 1=1--". This is a critical security vulnerability that allows attackers to bypass authentication without knowing valid credentials.

============================================================
🏁 FINAL ASSESSMENT RESULT:
============================================================
🚨 VULNERABILITY DETECTED! The SQL injection attack was successful. The page now shows "Welcome to the Dashboard!" and "Login successful! You are now authenticated" which confirms that authentication was bypassed using the SQL injection payload "' OR 1=1--". This is a critical security vulnerability that allows attackers to bypass authentication without knowing valid credentials.
============================================================
🧹 Cleaning up browser session...
```

## ⚙️ Configuration Options

### Browser Settings

Modify the `SessionConfig` in the agent:

```python
config = SessionConfig(
    headless=True,          # Run in headless mode
    timeout=30000,          # Timeout in milliseconds
    viewport={"width": 1920, "height": 1080}
)
```

### LLM Settings

Change the model or parameters:

```python
llm = ChatOpenAI(
    model="gpt-4",          # or "gpt-3.5-turbo"
    temperature=0,          # For consistent results
    openai_api_key=os.getenv("OPENAI_API_KEY")
)
```

## 🔒 Security Considerations

**⚠️ IMPORTANT**: This tool is for educational and authorized security testing only!

- Only test applications you own or have explicit permission to test
- The included test server is intentionally vulnerable for demonstration
- Never use this on production systems without proper authorization
- SQL injection testing can cause data loss or corruption
- Always follow responsible disclosure practices

## 🐛 Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not found"**

   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. **Playwright browser not found**

   ```bash
   playwright install chromium
   ```

3. **Tool execution errors**

   - Check if the target URL is accessible
   - Verify CSS selectors are correct
   - Try running with `headless=False` for debugging

4. **Agent not finding forms**
   - Ensure the page has loaded completely
   - Check if forms are in iframes
   - Try increasing timeout values

### Debug Mode

To see the browser in action, modify `playwright_interface.py` line 31:

```python
headless: bool = False  # Change from True to False
```

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the agent's capabilities:

- Add support for more injection types (XSS, LDAP, etc.)
- Improve form detection algorithms
- Add support for multi-step authentication
- Enhance reporting and screenshot capabilities

## 📄 License

This project is for educational purposes. Use responsibly and only on systems you own or have explicit permission to test.
