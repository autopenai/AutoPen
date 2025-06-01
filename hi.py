import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# === Tool Metadata for MCP ===
def tool_metadata():
    return {
        "name": "secret_scanner",
        "description": "Scans a website for exposed secrets in public JavaScript files. Can target a specific path or defaults to Next.js static chunks.",
        "parameters": {
            "url": {
                "type": "string",
                "description": "Base URL of the deployed site (e.g., https://example.com)"
            },
            "js_path_filter": {
                "type": "string",
                "description": "Optional string to filter JavaScript file paths (e.g., '/static/', '/assets/'). Defaults to Next.js '/_next/static/'.",
                "default": "/_next/static/"
            }
        }
    }

# === Tool Execution Function ===
def run(url: str, js_path_filter: str = "/_next/static/") -> dict:
    try:
        print(f"Scanning {url} for exposed secrets... (filter: {js_path_filter})")

        # Step 1: Fetch HTML and collect relevant script sources
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        script_urls = []
        for script in soup.find_all("script", src=True):
            src = script['src']
            if js_path_filter in src and src.endswith(".js"):
                full_url = src if src.startswith("http") else urljoin(url, src)
                script_urls.append(full_url)

        print(f"Found {len(script_urls)} JS files matching filter")

        # Step 2: Secret pattern definitions
        patterns = {
            "stripe_key": re.compile(r"sk_(live|test)_[0-9a-zA-Z]+"),
            "next_public_var": re.compile(r"NEXT_PUBLIC_[A-Z0-9_]+"),
            "firebase_keywords": re.compile(r"(firebase|apiKey|authDomain|projectId)", re.IGNORECASE),
            "bearer_token": re.compile(r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*", re.IGNORECASE),
            "generic_secrets": re.compile(r"(SECRET|password|token)", re.IGNORECASE),
        }

        findings = []

        # Step 3: Download and scan each script
        for js_url in script_urls:
            try:
                js_response = requests.get(js_url, timeout=10)
                content = js_response.text

                for pattern_name, regex in patterns.items():
                    matches = regex.findall(content)
                    if matches:
                        findings.append({
                            "file": js_url,
                            "pattern": pattern_name,
                            "matches": list(set(matches))
                        })

            except Exception as e:
                findings.append({
                    "file": js_url,
                    "error": f"Unable to scan file: {str(e)}"
                })

        return {
            "status": "success",
            "base_url": url,
            "filter": js_path_filter,
            "chunks_scanned": len(script_urls),
            "findings": findings or "No exposed secrets detected."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
