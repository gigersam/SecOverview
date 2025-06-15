from django.conf import settings
from .models import DNSQuery, DNSRecord
import dns.resolver
import dns.zone
import dns.query

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