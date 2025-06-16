import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from ..models import WebTechFingerprinting_Scan, WebTechFingerprinting_Results

FINGERPRINTS = [
    # Headers
    {"name": "Apache", "type": "header", "key": "Server", "pattern": r"Apache(?:/([\d\.]+))?", "version_group_index": 1},
    {"name": "Nginx", "type": "header", "key": "Server", "pattern": r"nginx(?:/([\d\.]+))?", "version_group_index": 1},
    {"name": "IIS", "type": "header", "key": "Server", "pattern": r"Microsoft-IIS(?:/([\d\.]+))?", "version_group_index": 1},
    {"name": "LiteSpeed", "type": "header", "key": "Server", "pattern": r"LiteSpeed"},
    {"name": "Cloudflare", "type": "header", "key": "Server", "pattern": r"cloudflare"},
    {"name": "Akamai", "type": "header", "key": "Server", "pattern": r"AkamaiGHost"}, # Old, but still seen
    {"name": "Akamai", "type": "header", "key": "X-Akamai-Transformed", "pattern": r".+"},


    {"name": "PHP", "type": "header", "key": "X-Powered-By", "pattern": r"PHP(?:/([\d\.\-]+))?", "version_group_index": 1},
    {"name": "PHP", "type": "header", "key": "Set-Cookie", "pattern": r"PHPSESSID="},
    {"name": "ASP.NET", "type": "header", "key": "X-Powered-By", "pattern": r"ASP\.NET"},
    {"name": "ASP.NET", "type": "header", "key": "X-ASPNET-Version", "pattern": r"([\d\.]+)", "version_group_index": 1},
    {"name": "ASP.NET", "type": "header", "key": "Set-Cookie", "pattern": r"ASPSESSIONID|ASP\.NET_SessionId"},
    {"name": "Java/JSP", "type": "header", "key": "Set-Cookie", "pattern": r"JSESSIONID"},
    {"name": "Ruby on Rails", "type": "header", "key": "Set-Cookie", "pattern": r"_rails_session|_session_id"},
    {"name": "ExpressJS (Node.js)", "type": "header", "key": "X-Powered-By", "pattern": r"Express"},

    # Meta Tags
    {"name": "WordPress", "type": "meta", "key": "generator", "pattern": r"WordPress\s*([\d\.]+)?", "version_group_index": 1},
    {"name": "Joomla", "type": "meta", "key": "generator", "pattern": r"Joomla!?\s*([\d\.]*)", "version_group_index": 1},
    {"name": "Drupal", "type": "meta", "key": "generator", "pattern": r"Drupal\s*([\d\.]+)", "version_group_index": 1},
    {"name": "Shopify", "type": "meta", "key": "shopify-checkout-api-token", "pattern": r".+"}, # Key presence is enough

    # HTML Content (general patterns, script includes, comments)
    {"name": "WordPress", "type": "html_content", "pattern": r"/wp-content/|/wp-includes/"},
    {"name": "WordPress", "type": "html_content", "pattern": r"<!-- Powered by WordPress"},
    {"name": "Joomla", "type": "html_content", "pattern": r"/media/jui/|/media/system/"},
    {"name": "Joomla", "type": "html_content", "pattern": r"<!-- Joomla! - Open Source Content Management"},
    {"name": "Drupal", "type": "html_content", "pattern": r"sites/default/files/|jQuery\.extend\(Drupal\.settings"},
    {"name": "Magento", "type": "html_content", "pattern": r"/skin/frontend/|static/frontend/|window\.authenticationPopup"},
    {"name": "Shopify", "type": "html_content", "pattern": r"cdn\.shopify\.com"},

    # Script SRC attributes
    {"name": "jQuery", "type": "script_src", "pattern": r"jquery(?:-[\d\.]*|-latest)?(?:\.min)?\.js", "version_group_index": None}, # Version often in filename
    {"name": "React", "type": "script_src", "pattern": r"react(?:-dom)?(?:\.min|\.development)?\.js"},
    {"name": "React", "type": "html_content", "pattern": r"data-reactroot|data-reactid"},
    {"name": "AngularJS", "type": "script_src", "pattern": r"angular(?:\.min)?\.js"},
    {"name": "AngularJS", "type": "html_content", "pattern": r"ng-app|ng-model|ng-controller"}, # Attributes
    {"name": "Vue.js", "type": "script_src", "pattern": r"vue(?:\.min|\.common|\.runtime)?\.js"},
    {"name": "Vue.js", "type": "html_content", "pattern": r"v-app|data-v-"}, # Attributes

    # robots.txt content (useful for CMS admin paths)
    {"name": "WordPress", "type": "robots_txt", "pattern": r"Disallow:\s*/wp-admin/"},
    {"name": "Joomla", "type": "robots_txt", "pattern": r"Disallow:\s*/administrator/"},
    {"name": "Drupal", "type": "robots_txt", "pattern": r"Disallow:\s*/user/login"},

    # Cookies (beyond session IDs already covered by headers)
    {"name": "Cloudflare", "type": "cookie", "key": "__cfduid", "pattern": r".*"}, # Old, but still might appear
    {"name": "Cloudflare", "type": "cookie", "key": "cf_clearance", "pattern": r".*"},
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 TechFingerprinter/1.0"
REQUEST_TIMEOUT = 10 # seconds

def fetch_url_content(url, is_robots_txt=False):
    """Fetches URL content and headers."""
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        # For robots.txt, we only care about text content
        if is_robots_txt:
            return response.text, None, None # content, headers, soup

        # For regular pages, get headers, text, and soup
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            soup = BeautifulSoup(response.text, 'html.parser')
            return response.text, response.headers, soup
        else: # Non-HTML content
            return response.text, response.headers, None

    except requests.exceptions.RequestException as e:
        print(f"[!] Error fetching {url}: {e}")
        return None, None, None

def analyze_technologies(url):
    """Analyzes a URL for web technologies."""
    found_tech = {} # Using a dict to store tech name and version if found

    def add_tech(name, version=None):
        if name not in found_tech or (version and not found_tech[name]):
            found_tech[name] = version if version else "Detected"
        elif version and found_tech[name] == "Detected": # Update if we find a specific version later
            found_tech[name] = version

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # --- 1. Analyze main page ---
    print(f"[*] Analyzing main page: {url}")
    html_content, response_headers, soup = fetch_url_content(url)

    if not response_headers and not html_content: # Complete failure to fetch
        return found_tech

    # --- 2. Analyze robots.txt ---
    parsed_url = urlparse(url)
    robots_url = urljoin(f"{parsed_url.scheme}://{parsed_url.netloc}", "robots.txt")
    print(f"[*] Checking: {robots_url}")
    robots_content, _, _ = fetch_url_content(robots_url, is_robots_txt=True)


    for fp in FINGERPRINTS:
        name = fp["name"]
        fp_type = fp["type"]
        pattern = fp["pattern"]
        key = fp.get("key")
        version_idx = fp.get("version_group_index")

        try:
            # --- Header Checks ---
            if fp_type == "header" and response_headers:
                if key in response_headers:
                    header_value = response_headers[key]
                    match = re.search(pattern, header_value, re.IGNORECASE)
                    if match:
                        version = match.group(version_idx) if version_idx and len(match.groups()) >= version_idx else None
                        add_tech(name, version)
                # Some headers can appear multiple times (e.g., Set-Cookie)
                elif key == "Set-Cookie" and key in response_headers.get('set-cookie', ''): # requests combines them
                    all_cookies_header = response_headers.get('set-cookie', '')
                    match = re.search(pattern, all_cookies_header, re.IGNORECASE)
                    if match:
                         add_tech(name) # Version usually not in cookie name pattern this way

            # --- Cookie Checks (from Set-Cookie headers) ---
            elif fp_type == "cookie" and response_headers:
                cookies_header = response_headers.get('Set-Cookie', '')
                # Example: PHPSESSID=...; path=/; HttpOnly, AnotherCookie=...
                # We need to check each cookie name.
                # A simple regex on the whole string is easier here for common patterns.
                if key: # if specific cookie name to check
                     cookie_pattern = rf"{re.escape(key)}=([^;]+)"
                     match = re.search(cookie_pattern, cookies_header, re.IGNORECASE)
                     if match:
                          add_tech(name) # Could try to match value with fp['pattern'] if needed
                elif re.search(pattern, cookies_header, re.IGNORECASE): # General pattern on cookies_header
                     add_tech(name)


            # --- Meta Tag Checks ---
            elif fp_type == "meta" and soup:
                if key:
                    meta_tag = soup.find("meta", attrs={"name": key})
                    if meta_tag and meta_tag.get("content"):
                        match = re.search(pattern, meta_tag["content"], re.IGNORECASE)
                        if match:
                            version = match.group(version_idx) if version_idx and len(match.groups()) >= version_idx else None
                            add_tech(name, version)

            # --- HTML Content Checks (including comments) ---
            elif fp_type == "html_content" and html_content:
                match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL) # DOTALL for multi-line comments
                if match:
                    version = match.group(version_idx) if version_idx and len(match.groups()) >= version_idx else None
                    add_tech(name, version)


            # --- Script SRC Checks ---
            elif fp_type == "script_src" and soup:
                for script_tag in soup.find_all("script", src=True):
                    src_value = script_tag["src"]
                    match = re.search(pattern, src_value, re.IGNORECASE)
                    if match:
                        # Try to extract version from filename if not specified by version_idx
                        # Example: jquery-3.6.0.min.js
                        version_from_filename_match = re.search(r"([\d\.]+)", match.group(0)) # match.group(0) is the full matched src part
                        version = None
                        if version_idx and len(match.groups()) >= version_idx:
                            version = match.group(version_idx)
                        elif version_from_filename_match:
                            version = version_from_filename_match.group(1)
                        add_tech(name, version)

            # --- robots.txt Content Checks ---
            elif fp_type == "robots_txt" and robots_content:
                match = re.search(pattern, robots_content, re.IGNORECASE)
                if match:
                    add_tech(name) # Version not typically in robots.txt patterns

        except Exception as e:
            # print(f"[!] Error processing fingerprint for {name} ({fp_type}): {e}")
            continue # Skip to next fingerprint if one causes an error

    if found_tech:
        webtechfingerprintscan = WebTechFingerprinting_Scan.objects.create(domain=url)
        for tech, version in found_tech.items():
            if version and version != "Detected":
                WebTechFingerprinting_Results.objects.create(
                    domain=webtechfingerprintscan,
                    technologie=tech,
                    version=version
                )
            else:
                WebTechFingerprinting_Results.objects.create(
                    domain=webtechfingerprintscan,
                    technologie=tech,
                    version=None
                )

    return webtechfingerprintscan