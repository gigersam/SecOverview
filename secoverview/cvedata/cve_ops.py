import json
import requests
import zipfile
import io
from .models import CveItem
from pathlib import Path
from datetime import datetime

def download_and_extract_cve_zips(start_year=2002, end_year=None, download_dir='./cvedata/cve_data'):
    """
    Download and unzip all NVD CVE JSON zip files from start_year up to end_year (inclusive).
    Files are saved/unzipped into download_dir. Yearly Zip-Files are created once a day at midnight.
    """
    if end_year is None:
        end_year = datetime.now().year

    dest_path = Path(download_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    for year in range(start_year, end_year + 1):
        zip_filename = f"nvdcve-2.0-{year}.json.zip"
        url = f"https://nvd.nist.gov/feeds/json/cve/2.0/{zip_filename}"
        print(f"Downloading {url}...")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            print(f"Extracting {zip_filename}...")
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                zf.extractall(dest_path)
            print(f"Saved JSON for {year} to {download_dir}")
        else:
            print(f"Failed to download {zip_filename}: HTTP {response.status_code}")

def load_cve_data(file_path):
    """
    Load CVE data from NVDCVE JSON and populate the CveItem table.
    Usage: load_cve_data('/path/to/nvdcve-2.0-recent.json')
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for vuln in data.get('vulnerabilities', []):
        cve = vuln.get('cve', {})
        item, created = CveItem.objects.update_or_create(
            cve_id=cve.get('id'),
            defaults={
                'source_identifier': cve.get('sourceIdentifier'),
                'published': cve.get('published'),
                'last_modified': cve.get('lastModified'),
                'vuln_status': cve.get('vulnStatus'),
                'descriptions': {d['lang']: d['value'] for d in cve.get('descriptions', [])},
                'metrics': cve.get('metrics', {}),
                'weaknesses': [w.get('description', []) for w in cve.get('weaknesses', [])],
                'configurations':  cve.get('configurations', {}),
                'references': [{ 'url': r.get('url'), 'source': r.get('source') } for r in cve.get('references', [])],
            }
        )
        #if created:
        #    print(f"Created CVE record {item.cve_id}")
        #else:
        #    print(f"Updated CVE record {item.cve_id}")
#
def load_all_cve_data(directory_path='./cvedata/cve_data'):
    """
    Iterate through all JSON files in the given directory and load each into the database.
    Usage: load_all_cve_data('./cve_data')
    """
    # Using pathlib
    for path in Path(directory_path).glob('*.json'):
        print(f"Processing {path}")
        load_cve_data(str(path))

def get_load_all_cve_data():
    download_and_extract_cve_zips()
    load_all_cve_data()

