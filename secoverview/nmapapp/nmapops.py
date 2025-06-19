from .models import NmapAssets, Nmapscan, AssetsNmapscan
import nmap
import json

def parse_cpe_info(cpe_str):
    if cpe_str == None:
        return None, None, None, None, None, None, None
    if not cpe_str.startswith("cpe:/"):
        raise ValueError("Unsupported CPE format: must start with cpe:/")

    # Remove 'cpe:/'
    parts = cpe_str[5:].split(':')

    if len(parts) < 3:
        raise ValueError("Malformed CPE string")

    part_type_map = {'a': 'application', 'o': 'operating_system', 'h': 'hardware'}
    part = parts[0]
    cpe_type = part_type_map.get(part, 'unknown')

    return cpe_type, parts[1] if len(parts) > 1 else None, parts[2] if len(parts) > 2 else None, parts[3] if len(parts) > 3 else None,parts[4] if len(parts) > 4 else None, parts[5] if len(parts) > 5 else None, parts[6] if len(parts) > 6 else None

def execute_nmap_scan(ip, parameters):
    scanner = nmap.PortScanner()
    # Scan the subnet with service detection
    scanner.scan(hosts=ip, arguments=parameters)
    combined = []
    for host in scanner.all_hosts():
        combined.append(scanner[host])
    return combined
    
def execute_nmap_scan_db(ip, parameters):
    result = execute_nmap_scan(ip, parameters)
    json_data_dump = json.dumps(result, indent=4)
    scanconfig = Nmapscan.objects.create(data=json_data_dump, ip=ip, parameters=parameters)

    for data_obj in result:
        ip_address = data_obj.get("addresses", {}).get("ipv4")
        hostnames = data_obj.get("hostnames", [])
        hostname = hostnames[0].get("name") if hostnames else ""

        asset = NmapAssets.objects.update_or_create(hostname=hostname, ip_address=ip_address, defaults={"added_by_scan": scanconfig, "json_data": json.dumps(data_obj, indent=4)})
        AssetsNmapscan.objects.create(assets=asset[0], assets_json_data=data_obj, nmapscan=scanconfig)
    
    return result
