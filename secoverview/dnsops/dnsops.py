from django.conf import settings
from .models import DNSQuery, DNSRecord
import dns.resolver
import dns.zone
import dns.query
import itertools
import random

# Keyboard adjacency map for QWERTY layout (simplified)
keyboard_adjacent = {
    'a': ['q', 'w', 's', 'z'],
    'b': ['v', 'g', 'h', 'n'],
    'c': ['x', 'd', 'f', 'v'],
    'd': ['s', 'e', 'r', 'f', 'c', 'x'],
    'e': ['w', 's', 'd', 'r'],
    'f': ['d', 'r', 't', 'g', 'v', 'c'],
    'g': ['f', 't', 'y', 'h', 'b', 'v'],
    'h': ['g', 'y', 'u', 'j', 'n', 'b'],
    'i': ['u', 'j', 'k', 'o'],
    'j': ['h', 'u', 'i', 'k', 'm', 'n'],
    'k': ['j', 'i', 'o', 'l', 'm'],
    'l': ['k', 'o', 'p'],
    'm': ['n', 'j', 'k'],
    'n': ['b', 'h', 'j', 'm'],
    'o': ['i', 'k', 'l', 'p'],
    'p': ['o', 'l'],
    'q': ['w', 'a'],
    'r': ['e', 'd', 'f', 't'],
    's': ['a', 'w', 'e', 'd', 'x', 'z'],
    't': ['r', 'f', 'g', 'y'],
    'u': ['y', 'h', 'j', 'i'],
    'v': ['c', 'f', 'g', 'b'],
    'w': ['q', 'a', 's', 'e'],
    'x': ['z', 's', 'd', 'c'],
    'y': ['t', 'g', 'h', 'u'],
    'z': ['a', 's', 'x']
}

# Homoglyph map (partial)
homoglyphs = {
    'a': ['à', 'á', 'â', 'ä', 'æ', 'ɑ'],
    'e': ['è', 'é', 'ê', 'ë', 'ē', 'ė', 'ę'],
    'i': ['ì', 'í', 'î', 'ï', 'ī', 'į', 'ı'],
    'o': ['ò', 'ó', 'ô', 'ö', 'ø', 'ō'],
    'u': ['ù', 'ú', 'û', 'ü', 'ū'],
    'c': ['ç', 'ć', 'č'],
    's': ['ś', 'š', 'ş'],
    'n': ['ñ', 'ń']
}

# Wordlists: https://github.com/danielmiessler/SecLists/blob/master/Discovery/DNS/
def get_dns_wordlist_data():
    if settings.DNS_WORDLIST_DEFAULT != "":
        with open(f'dnsops/domainlists/{settings.DNS_WORDLIST_DEFAULT}', 'r') as file:
            return [line.strip() for line in file]
    else:
        return ["www", "mail", "ftp", "api", "blog", "dev", "test", "staging", "support", "shop"]


def enumerate_dns_records(domain):
    results = {}
    query = DNSQuery.objects.create(domain=domain)
    for record_type in DNSRecord.RECORD_TYPES:
        record_type = record_type[0]
        try:
            answers = dns.resolver.resolve(domain, record_type)
            results[record_type] = [str(record) for record in answers]
            for record in answers:
                DNSRecord.objects.create(query=query, record_type=record_type, value=str(record), ttl=3600)
        except:
            pass

    subdomain_results = {}
    subdomain_results[domain] = results
    subdomain_list = get_dns_wordlist_data()
    for subdomain in subdomain_list:
        full_domain = f"{subdomain}.{domain}"
        subdomain_records = {}
        query = DNSQuery.objects.create(domain=full_domain)

        for record_type in DNSRecord.RECORD_TYPES:
            record_type = record_type[0]
            try:
                answers = dns.resolver.resolve(full_domain, record_type)
                subdomain_records[record_type] = [str(record) for record in answers]
                for record in answers:
                    DNSRecord.objects.create(query=query, record_type=record_type, value=str(record), ttl=3600)
            except:
                pass
        
        if subdomain_records:
            subdomain_results[full_domain] = subdomain_records
    
    return subdomain_results

def generate_variants(domain):
    domain_name, tld = domain.split('.', 1)
    variants = set()

    # Swap adjacent letters
    for i in range(len(domain_name) - 1):
        swapped = list(domain_name)
        swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
        variants.add("".join(swapped) + '.' + tld)

    # Remove one letter
    for i in range(len(domain_name)):
        variants.add(domain_name[:i] + domain_name[i+1:] + '.' + tld)

    # Add random letter
    for i in range(len(domain_name) + 1):
        for c in 'abcdefghijklmnopqrstuvwxyz':
            variants.add(domain_name[:i] + c + domain_name[i:] + '.' + tld)

    # Replace with keyboard-adjacent keys
    for i, ch in enumerate(domain_name):
        if ch in keyboard_adjacent:
            for adj in keyboard_adjacent[ch]:
                variants.add(domain_name[:i] + adj + domain_name[i+1:] + '.' + tld)

    # Replace with homoglyphs
    for i, ch in enumerate(domain_name):
        if ch in homoglyphs:
            for glyph in homoglyphs[ch]:
                variants.add(domain_name[:i] + glyph + domain_name[i+1:] + '.' + tld)

    return sorted(variants)