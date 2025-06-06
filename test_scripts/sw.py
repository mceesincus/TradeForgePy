import requests
from bs4 import BeautifulSoup
import re
import json
import yaml
from urllib.parse import urljoin, urlparse

def fetch_and_parse_spec(spec_url, headers=None):
    """
    Fetches a spec file from a URL and tries to parse it as JSON or YAML.
    """
    if headers is None:
        headers = {'Accept': 'application/json, application/x-yaml, text/yaml, */*'}
    print(f"Attempting to fetch spec from: {spec_url}")
    try:
        response = requests.get(spec_url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            content = response.text
            content_type = response.headers.get('Content-Type', '').lower()

            # Try JSON
            if 'json' in content_type or spec_url.endswith('.json'):
                try:
                    spec_data = json.loads(content)
                    if isinstance(spec_data, dict) and ('openapi' in spec_data or 'swagger' in spec_data):
                        print(f"Successfully parsed JSON spec from {spec_url}")
                        return spec_data, 'json'
                except json.JSONDecodeError:
                    pass # Will try YAML or guess

            # Try YAML
            if 'yaml' in content_type or 'yml' in content_type or spec_url.endswith(('.yaml', '.yml')):
                try:
                    spec_data = yaml.safe_load(content)
                    if isinstance(spec_data, dict) and ('openapi' in spec_data or 'swagger' in spec_data):
                        print(f"Successfully parsed YAML spec from {spec_url}")
                        return spec_data, 'yaml'
                except yaml.YAMLError:
                    pass # Will try to guess

            # If content type wasn't definitive, try to guess based on content
            try:
                spec_data_json = json.loads(content)
                if isinstance(spec_data_json, dict) and ('openapi' in spec_data_json or 'swagger' in spec_data_json):
                    print(f"Successfully parsed (guessed JSON) spec from {spec_url}")
                    return spec_data_json, 'json'
            except json.JSONDecodeError:
                try:
                    spec_data_yaml = yaml.safe_load(content)
                    if isinstance(spec_data_yaml, dict) and ('openapi' in spec_data_yaml or 'swagger' in spec_data_yaml):
                        print(f"Successfully parsed (guessed YAML) spec from {spec_url}")
                        return spec_data_yaml, 'yaml'
                except yaml.YAMLError:
                    print(f"Could not parse content from {spec_url} as JSON or YAML.")
                    return None, None
        else:
            print(f"Failed to fetch spec from {spec_url}. Status: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching spec from {spec_url}: {e}")
    return None, None


def find_spec_in_doc_ui(base_urls):
    """
    Tries to find links to OpenAPI/Swagger spec files within common API documentation UI pages.

    Args:
        base_urls (list): A list of base URLs for the API.

    Returns:
        tuple: (spec_content, found_url, format) or (None, None, None) if not found.
    """
    common_ui_paths = [
        "", # Check the base URL itself
        "swagger",
        "swagger-ui",
        "swagger-ui.html",
        "api-docs",
        "docs",
        "redoc",
        "redoc.html",
        "developer",
        "developers",
        "api/docs",
        "api/swagger",
        "api/swagger-ui.html",
    ]

    # Regex patterns to find spec URLs within HTML/JS content
    # Accounts for "url": "spec.json", url: "spec.json", url: 'spec.json', etc.
    spec_link_patterns = [
        re.compile(r'"url"\s*:\s*["\']([^"\']+\.(?:json|yaml|yml))["\']', re.IGNORECASE), # SwaggerUIBundle config
        re.compile(r'spec-url=["\']([^"\']+\.(?:json|yaml|yml))["\']', re.IGNORECASE),    # Redoc tag attribute
        re.compile(r'href=["\']([^"\']+\.(?:json|yaml|yml))["\']', re.IGNORECASE),       # Standard href links
        re.compile(r'src=["\']([^"\']+\.(?:json|yaml|yml))["\']', re.IGNORECASE),        # Sometimes in src for iframes/scripts
        re.compile(r'const\s+\w+\s*=\s*["\']([^"\']+\.(?:json|yaml|yml))["\']', re.IGNORECASE), # JS const assignment
    ]

    html_headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

    for base_url in base_urls:
        # Ensure base_url does not end with a slash for consistent joining
        clean_base_url = base_url.rstrip('/')

        for ui_path in common_ui_paths:
            page_url_to_try = f"{clean_base_url}/{ui_path.lstrip('/')}" if ui_path else clean_base_url
            # Avoid double slashes if ui_path is empty and base_url ended with /
            if page_url_to_try.endswith("//") and not page_url_to_try.endswith("://"):
                 page_url_to_try = page_url_to_try.rstrip('/')

            print(f"Trying UI page: {page_url_to_try}")
            try:
                response = requests.get(page_url_to_try, headers=html_headers, timeout=10, allow_redirects=True)
                if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', '').lower():
                    page_content = response.text
                    found_spec_urls = set()

                    # Search in the HTML content itself (e.g., in script tags or attributes)
                    for pattern in spec_link_patterns:
                        for match in pattern.finditer(page_content):
                            spec_path_segment = match.group(1)
                            found_spec_urls.add(spec_path_segment)

                    # Search for specific script tags like SwaggerUIBundle initialization
                    soup = BeautifulSoup(page_content, 'html.parser')
                    scripts = soup.find_all('script')
                    for script in scripts:
                        script_content = script.string if script.string else ""
                        # Also check src attribute of script tags
                        if script.get('src'):
                             # If src itself is a spec file
                            if script.get('src').endswith(('.json', '.yaml', '.yml')):
                                found_spec_urls.add(script.get('src'))
                             # Else, if it's a JS file that might contain the spec URL
                            else:
                                try:
                                    js_url = urljoin(page_url_to_try, script.get('src'))
                                    print(f"  Fetching external JS: {js_url}")
                                    js_response = requests.get(js_url, timeout=5)
                                    if js_response.status_code == 200:
                                        script_content += js_response.text # Append external JS content
                                except requests.RequestException:
                                    pass # Ignore errors fetching external JS

                        for pattern in spec_link_patterns:
                            for match in pattern.finditer(script_content):
                                spec_path_segment = match.group(1)
                                found_spec_urls.add(spec_path_segment)

                    # Process found potential spec URLs
                    for spec_path_segment in found_spec_urls:
                        # Construct full URL:
                        # 1. If it's already a full URL
                        if urlparse(spec_path_segment).scheme:
                            absolute_spec_url = spec_path_segment
                        # 2. If it's an absolute path from the server root
                        elif spec_path_segment.startswith('/'):
                            parsed_page_url = urlparse(page_url_to_try)
                            absolute_spec_url = f"{parsed_page_url.scheme}://{parsed_page_url.netloc}{spec_path_segment}"
                        # 3. If it's a relative path
                        else:
                            absolute_spec_url = urljoin(page_url_to_try, spec_path_segment)

                        # Clean up URL (e.g. remove ../)
                        absolute_spec_url = requests.utils.requote_uri(absolute_spec_url)


                        print(f"  Potential spec link found: {spec_path_segment} -> Resolved to: {absolute_spec_url}")
                        spec_data, spec_format = fetch_and_parse_spec(absolute_spec_url)
                        if spec_data:
                            return spec_data, absolute_spec_url, spec_format

            except requests.RequestException as e:
                print(f"Error trying UI page {page_url_to_try}: {e}")
                continue
    return None, None, None


# --- Example Usage for TopStepX (based on your docs) ---
api_base_urls_for_ui_check = [
    "https://api.topstepx.com",  # Production API Endpoint
    "https://gateway-api-demo.s2f.projectx.com", # Demo Gateway
    # You can add more variations if you suspect subdomains or specific developer portals
    # "https://developer.topstepx.com",
    # "https://docs.topstepx.com",
]

print("\n--- Method 2: Checking Common API Documentation UI Paths ---")
spec_content_ui, found_url_ui, spec_format_ui = find_spec_in_doc_ui(api_base_urls_for_ui_check)

if spec_content_ui:
    print(f"\nSuccessfully found OpenAPI/Swagger specification ({spec_format_ui}) via UI page inspection.")
    print(f"Specification URL: {found_url_ui}")

    # Example: Save to file
    filename_ui = f"openapi_from_ui.{spec_format_ui}"
    with open(filename_ui, 'w', encoding='utf-8') as f:
        if spec_format_ui == 'json':
            json.dump(spec_content_ui, f, indent=2)
        else:
            yaml.dump(spec_content_ui, f, indent=2, allow_unicode=True)
    print(f"Specification saved to {filename_ui}")

    # And then use it with datamodel-codegen:
    # e.g., datamodel-codegen --input openapi_from_ui.json --output generated_models.py
else:
    print("\nCould not automatically find an OpenAPI/Swagger specification by inspecting common UI pages.")