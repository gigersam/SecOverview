import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

# Regex patterns
EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_REGEX = r"\+?\d[\d\-\s().]{7,}\d"
NAME_REGEX = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"

def is_valid_url(url, base_domain):
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and base_domain in parsed.netloc

def extract_info(text):
    emails = set(re.findall(EMAIL_REGEX, text))
    phones = set(re.findall(PHONE_REGEX, text))
    names = set(re.findall(NAME_REGEX, text))
    return emails, phones, names

def crawl_and_scrape(start_url, max_pages=50):
    visited = set()
    queue = deque([start_url])
    base_domain = urlparse(start_url).netloc
    found_emails, found_phones, found_names = set(), set(), set()

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            print(f"[+] Crawling: {url}")
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            text = soup.get_text()
            emails, phones, names = extract_info(text)
            found_emails.update(emails)
            found_phones.update(phones)
            found_names.update(names)

            for link in soup.find_all("a", href=True):
                abs_url = urljoin(url, link["href"])
                if is_valid_url(abs_url, base_domain) and abs_url not in visited:
                    queue.append(abs_url)

        except Exception as e:
            print("[-] Error:", e)
