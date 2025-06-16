
import urllib.request
import ssl
import socket
from urllib.error import URLError, HTTPError

# Recommended minimum HSTS max-age (e.g., 1 year = 31536000 seconds)
RECOMMENDED_HSTS_MAX_AGE = 31536000 # 1 year
# A lower but still acceptable value for initial deployments
ACCEPTABLE_HSTS_MAX_AGE = 15552000 # 6 months

# --- Helper function to parse HSTS ---
def parse_hsts_header(header_value):
    directives = {}
    if not header_value:
        return directives
    parts = [part.strip().lower() for part in header_value.split(';')]
    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            directives[key] = value
        else:
            directives[part] = True # For directives like includeSubDomains, preload
    return directives

def check_security_headers(url_to_check):
    """
    Fetches a URL and checks for common OWASP security headers.
    """
    results = {}
    print(f"[*] Checking security headers for: {url_to_check}")

    # Ensure we are checking HTTPS for HSTS and other relevant headers
    if not url_to_check.startswith("https://"):
        print("    [~] Warning: URL does not start with https://. HSTS is only effective over HTTPS.")
        print("    [~] Attempting to force HTTPS for the check.")
        if url_to_check.startswith("http://"):
            url_to_check = "https://" + url_to_check[len("http://"):]
        else:
            url_to_check = "https://" + url_to_check
        print(f"    [~] Checking: {url_to_check}")


    # Create a default SSL context (verifies certs by default)
    # For some self-signed certs or specific corporate environments, you might need to customize this
    # For public internet checks, default is usually what you want.
    context = ssl.create_default_context()
    # To ignore SSL certificate errors (NOT RECOMMENDED for production/security tools, but can be useful for testing internal sites):
    # context.check_hostname = False
    # context.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url_to_check, headers={'User-Agent': 'PythonSecurityHeaderChecker/1.0'})

    try:
        with urllib.request.urlopen(req, context=context, timeout=10) as response:
            headers = response.headers # This is an http.client.HTTPMessage object
            #print(f"    [+] Successfully fetched URL (Status: {response.status}). Final URL: {response.geturl()}")

            # 1. Strict-Transport-Security (HSTS)
            hsts_value = headers.get('Strict-Transport-Security')
            results['Strict-Transport-Security'] = {'present': bool(hsts_value), 'value': hsts_value, 'issues': []}
            if hsts_value:
                directives = parse_hsts_header(hsts_value)
                max_age_str = directives.get('max-age')
                if max_age_str:
                    try:
                        max_age = int(max_age_str)
                        if max_age < ACCEPTABLE_HSTS_MAX_AGE:
                            results['Strict-Transport-Security']['issues'].append(
                                f"max-age ({max_age}) is less than the acceptable {ACCEPTABLE_HSTS_MAX_AGE} seconds (approx. 6 months). Recommended: >= {RECOMMENDED_HSTS_MAX_AGE} (1 year)."
                            )
                        if 'includesubdomains' not in directives: # lowercase key from parse_hsts_header
                             results['Strict-Transport-Security']['issues'].append(
                                "'includeSubDomains' directive is missing."
                            )
                        # 'preload' is a strong recommendation if other criteria are met
                        if 'preload' not in directives:
                             results['Strict-Transport-Security']['issues'].append(
                                "'preload' directive is missing (consider adding if max-age is high and includeSubDomains is present)."
                            )
                    except ValueError:
                        results['Strict-Transport-Security']['issues'].append("max-age value is not a valid integer.")
                else:
                    results['Strict-Transport-Security']['issues'].append("max-age directive is missing, which is required for HSTS.")
            else:
                 results['Strict-Transport-Security']['issues'].append("Header not set.")


            # 2. X-Frame-Options
            xfo_value = headers.get('X-Frame-Options')
            results['X-Frame-Options'] = {'present': bool(xfo_value), 'value': xfo_value, 'issues': []}
            if xfo_value:
                if not xfo_value.upper() in ['DENY', 'SAMEORIGIN']:
                    results['X-Frame-Options']['issues'].append(
                        f"Value '{xfo_value}' is not 'DENY' or 'SAMEORIGIN'. Consider 'DENY' for max security."
                    )
            else:
                results['X-Frame-Options']['issues'].append("Header not set. Vulnerable to Clickjacking.")

            # 3. X-Content-Type-Options
            xcto_value = headers.get('X-Content-Type-Options')
            results['X-Content-Type-Options'] = {'present': bool(xcto_value), 'value': xcto_value, 'issues': []}
            if xcto_value:
                if xcto_value.lower() != 'nosniff':
                    results['X-Content-Type-Options']['issues'].append(
                        f"Value '{xcto_value}' is not 'nosniff'."
                    )
            else:
                results['X-Content-Type-Options']['issues'].append("Header not set. Should be 'nosniff'.")

            # 4. Content-Security-Policy (CSP)
            # CSP is complex. We'll mainly check for presence and if it's too permissive (e.g., 'unsafe-inline').
            # Full parsing is beyond a simple "native" script.
            csp_value = headers.get('Content-Security-Policy')
            results['Content-Security-Policy'] = {'present': bool(csp_value), 'value': csp_value, 'issues': []}
            if csp_value:
                if "'unsafe-inline'" in csp_value or "'unsafe-eval'" in csp_value:
                    results['Content-Security-Policy']['issues'].append(
                        "CSP contains 'unsafe-inline' or 'unsafe-eval' which significantly weakens its protection."
                    )
                if "default-src 'none'" in csp_value and len(csp_value.split(';')) < 3 : # Very restrictive, might break things but is secure
                     pass # This is strong
                elif "default-src" not in csp_value and "script-src" not in csp_value and "object-src" not in csp_value:
                     results['Content-Security-Policy']['issues'].append(
                        "CSP is present but lacks common protective directives like default-src, script-src, or object-src. Review policy carefully."
                    )
            else:
                results['Content-Security-Policy']['issues'].append("Header not set. Crucial for XSS mitigation.")
            
            # 5. Referrer-Policy
            rp_value = headers.get('Referrer-Policy')
            results['Referrer-Policy'] = {'present': bool(rp_value), 'value': rp_value, 'issues': []}
            common_safe_rp = ['no-referrer', 'same-origin', 'strict-origin', 'strict-origin-when-cross-origin']
            if rp_value:
                if rp_value.lower() not in common_safe_rp:
                     results['Referrer-Policy']['issues'].append(
                        f"Value '{rp_value}' might leak too much information. Consider one of: {', '.join(common_safe_rp)}."
                    )
            else:
                results['Referrer-Policy']['issues'].append("Header not set. Consider 'strict-origin-when-cross-origin' or stronger.")

            # 6. Permissions-Policy (formerly Feature-Policy)
            pp_value = headers.get('Permissions-Policy') or headers.get('Feature-Policy') # Check both
            policy_name = 'Permissions-Policy' if headers.get('Permissions-Policy') else 'Feature-Policy'
            results[policy_name] = {'present': bool(pp_value), 'value': pp_value, 'issues': []}
            if not pp_value:
                 results[policy_name]['issues'].append(
                    "Header not set. Useful for restricting browser feature access."
                )

            # 7. X-XSS-Protection (Legacy, but often still checked)
            xxssp_value = headers.get('X-XSS-Protection')
            results['X-XSS-Protection'] = {'present': bool(xxssp_value), 'value': xxssp_value, 'issues': []}
            if xxssp_value:
                if xxssp_value not in ['1; mode=block', '0']: # '0' disables it
                     results['X-XSS-Protection']['issues'].append(
                        f"Value '{xxssp_value}' is not '1; mode=block' (enable) or '0' (disable). Modern browsers often ignore this or CSP is preferred."
                    )
            # else: # Absence is fine if CSP is strong
            #     results['X-XSS-Protection']['issues'].append("Header not set. Largely superseded by CSP, but '1; mode=block' was common.")


            # 8. Clear-Site-Data
            csd_value = headers.get('Clear-Site-Data')
            results['Clear-Site-Data'] = {'present': bool(csd_value), 'value': csd_value, 'issues': []}
            # No specific value check, presence implies functionality on logout etc.
            # if not csd_value:
            #     results['Clear-Site-Data']['issues'].append("Header not set. Can be used to clear browsing data on logout.")

            # 9. Cross-Origin-Opener-Policy (COOP)
            coop_value = headers.get('Cross-Origin-Opener-Policy')
            results['Cross-Origin-Opener-Policy'] = {'present': bool(coop_value), 'value': coop_value, 'issues': []}
            if coop_value:
                if coop_value.lower() not in ['same-origin', 'same-origin-allow-popups', 'unsafe-none']:
                    results['Cross-Origin-Opener-Policy']['issues'].append(f"Value '{coop_value}' is not a standard COOP directive.")
            else:
                results['Cross-Origin-Opener-Policy']['issues'].append("Header not set. Consider 'same-origin' for process isolation.")

            # 10. Cross-Origin-Embedder-Policy (COEP)
            coep_value = headers.get('Cross-Origin-Embedder-Policy')
            results['Cross-Origin-Embedder-Policy'] = {'present': bool(coep_value), 'value': coep_value, 'issues': []}
            if coep_value:
                 if coep_value.lower() not in ['require-corp', 'unsafe-none', 'credentialless']:
                     results['Cross-Origin-Embedder-Policy']['issues'].append(f"Value '{coep_value}' is not a standard COEP directive.")
            else:
                results['Cross-Origin-Embedder-Policy']['issues'].append("Header not set. Needed with COOP for full cross-origin isolation. Consider 'require-corp'.")


    except HTTPError as e:
        print(f"    [!] HTTP Error: {e.code} {e.reason}")
        if e.headers: # Print headers even on error if available
            print("    --- Error Response Headers ---")
            for key, value in e.headers.items():
                print(f"    {key}: {value}")
            print("    ----------------------------")
    except URLError as e:
        if isinstance(e.reason, socket.gaierror):
            print(f"    [!] Naming or Address Resolution Error: {e.reason}")
        elif isinstance(e.reason, socket.timeout):
            print(f"    [!] Timeout Error: Could not connect to {url_to_check}")
        else:
            print(f"    [!] URL Error: {e.reason}")
    except socket.timeout:
        print(f"    [!] Timeout Error: Request timed out for {url_to_check}")
    except ssl.SSLCertVerificationError as e:
        print(f"    [!] SSL Certificate Verification Error: {e}")
        print(f"    [~] This might be a self-signed certificate or a misconfiguration.")
    except Exception as e:
        print(f"    [!] An unexpected error occurred: {e}")

    return results