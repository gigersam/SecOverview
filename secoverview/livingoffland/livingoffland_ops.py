import json
import requests
import zipfile
import io
import yaml
from pathlib import Path
from .models import (
    LOLBASBinary, LOLBASCommand, LOLBASTag, LOLBASFullPath,
    LOLBASDetection, LOLBASResource,
    GTFObinsBinary, GTFObinsFunction, GTFObinsFunctionExample
)


def get_lolbas_data():
    try:
        response = requests.get(url="https://lolbas-project.github.io/api/lolbas.json")
    except:
        print("Error fetching lolbas data")
        return 1

    data = response.json()
    print(data)
    for binary_data in data:
        binary, _ = LOLBASBinary.objects.update_or_create(
            name=binary_data.get("Name"),
            defaults={
                "description": binary_data.get("Description"),
                "author": binary_data.get("Author"),
                "created": binary_data.get("Created") or None,
                "url": binary_data.get("url"),
            },
        )
        # Commands
        LOLBASCommand.objects.filter(binary=binary).delete()
        for cmd in binary_data.get("Commands") or []:
            command = LOLBASCommand.objects.update_or_create(
                binary=binary,
                command=cmd.get("Command"),
                description=cmd.get("Description"),
                usecase=cmd.get("Usecase"),
                category=cmd.get("Category"),
                privileges=cmd.get("Privileges"),
                mitre_id=cmd.get("MitreID"),
                operating_system=cmd.get("OperatingSystem"),
            )
            for tag in cmd.get("Tags", []):
                for key, value in tag.items():
                    LOLBASTag.objects.get_or_create(command=command[0], key=key, value=value)
        # Full Path
        LOLBASFullPath.objects.filter(binary=binary).delete()
        for fp in binary_data.get("Full_Path") or []:
            LOLBASFullPath.objects.get_or_create(binary=binary, path=fp.get("Path"))
        # Detections
        LOLBASDetection.objects.filter(binary=binary).delete()
        for detect in binary_data.get("Detection") or []:
            for key, value in detect.items():
                LOLBASDetection.objects.get_or_create(binary=binary, key=key, value=value)
        # Resources
        LOLBASResource.objects.filter(binary=binary).delete()
        for resource in binary_data.get("Resources") or []:
            LOLBASResource.objects.get_or_create(binary=binary, link=resource.get("Link"))


def load_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        try:
            # Split into: "", frontmatter, rest
            _, fm, _ = text.split("---", 2)
        except ValueError:
            raise ValueError(f"No closing frontmatter delimiter in {path}")
        return yaml.safe_load(fm) or {}
    return yaml.safe_load(text) or {}

def get_gtfobins_data():
    download_dir = Path("./livingoffland/gtfobins/")
    dest_path = Path(download_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    zip_filename = "master.zip"
    url = "https://github.com/GTFOBins/GTFOBins.github.io/archive/refs/heads/master.zip"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        print(f"Extracting {zip_filename}...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            zf.extractall(dest_path)
        print(f"Saved gtfobins to {download_dir}")
    else:
        print(f"Failed to download {zip_filename}: HTTP {response.status_code}")

    pathtoyaml = Path("./livingoffland/gtfobins/GTFOBins.github.io-master/_gtfobins/")
    for yaml_file in pathtoyaml.glob("*.md"):
        binary_name = yaml_file.stem
        try:
            data = load_frontmatter(yaml_file)
        except Exception as e:
            print(f"Skipping {yaml_file}: {e}")
            continue
        binary, _ = GTFObinsBinary.objects.update_or_create(
            name=binary_name,
            defaults={"description": data.get("description")},
        )
        for function_name, examples in data.get("functions", {}).items():
            function, _ = GTFObinsFunction.objects.update_or_create(
                name=function_name,
            )
            # Remove old examples
            GTFObinsFunctionExample.objects.filter(binary=binary, function=function).delete()
            for example in examples:
                GTFObinsFunctionExample.objects.create(
                    binary=binary,
                    function=function,
                    description=example.get("description"),
                    code=example.get("code"),
                )