import requests
import json

# --- Configuration ---
CRTSH_URL = "https://crt.sh/"
DEFAULT_TIMEOUT = 30  # seconds for the HTTP request

# --- Main Logic ---
def query_crtsh(domain, timeout=DEFAULT_TIMEOUT):
    """
    Queries crt.sh for subdomains of a given domain.
    Returns a set of unique subdomains.
    """
    found_subdomains = set()
    # The %. prefix is important to match all subdomains
    query_domain = f"%.{domain.strip('.')}"
    url = f"{CRTSH_URL}json?q={query_domain}"

    headers = {
        'User-Agent': 'Python CrtSh Subdomain Querier/1.0'
    }

    print(f"[*] Querying crt.sh for: {query_domain}")

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        # crt.sh can return an empty response or non-JSON if no results,
        # or sometimes a single JSON object if only one cert, or a list.
        # It seems it consistently returns a list of JSON objects now.
        try:
            certs = response.json()
        except json.JSONDecodeError:
            if response.text.strip() == "":
                print("[*] crt.sh returned an empty response (no certificates found).")
                return found_subdomains
            else:
                print(f"[!] Failed to decode JSON from crt.sh. Response was: {response.text[:200]}...")
                return found_subdomains # Or raise an error

        if not isinstance(certs, list):
            print(f"[!] Unexpected response format from crt.sh (expected a list, got {type(certs)}).")
            return found_subdomains

        for cert_entry in certs:
            if isinstance(cert_entry, dict):
                # 'name_value' often contains multiple subdomains, newline-separated.
                # It includes Subject Alternative Names (SANs).
                if 'name_value' in cert_entry:
                    names = cert_entry['name_value'].split('\n')
                    for name in names:
                        name = name.strip().lower()
                        # Ensure it's a subdomain of the target and not a wildcard for a different domain
                        if name.endswith(f".{domain.lower()}") or name == domain.lower():
                             # Remove leading wildcard characters like '*.', but keep the rest
                            if name.startswith("*."):
                                name = name[2:] # Keep the wildcard entry as is, e.g. *.example.com
                            if name not in found_subdomains and name: # Add if not empty and unique
                                found_subdomains.add(name)

                # 'common_name' is usually a single domain.
                if 'common_name' in cert_entry:
                    name = cert_entry['common_name'].strip().lower()
                    if name.endswith(f".{domain.lower()}") or name == domain.lower():
                        if name.startswith("*."):
                            name = name[2:]
                        if name not in found_subdomains and name:
                            found_subdomains.add(name)

    except requests.exceptions.Timeout:
        print(f"[!] Timeout while querying crt.sh for {query_domain}")
    except requests.exceptions.RequestException as e:
        print(f"[!] Error querying crt.sh for {query_domain}: {e}")
    except Exception as e:
        print(f"[!] An unexpected error occurred: {e}")

    # Filter out the base domain itself if we only want true subdomains
    # and also remove duplicates that might arise from *.example.com vs example.com
    # after stripping *.
    final_subdomains = set()
    for sub in found_subdomains:
        final_subdomains = set()
        for sub_name in found_subdomains:
            # Add all names found that are related to the domain
            # This includes the domain itself, direct subdomains, and wildcard entries.
            final_subdomains.add(sub_name)

    return sorted(list(final_subdomains))
