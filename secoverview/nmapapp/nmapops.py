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