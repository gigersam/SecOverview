from django.db.models import Q
from nmapapp.models import NmapAssets, Nmapscan, AssetsNmapscan
from mlnids.models import NetworkFlow
from .models import *
from nmapapp.nmapops import parse_cpe_info
import json
import ipaddress

def is_internal_ip(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False

def gather_nmap_assets_infos():
    """Gather compute assets"""
    nmapassets = NmapAssets.objects.all()
    for asset in nmapassets:
        computeasset, flag = ComputeAssets.objects.update_or_create(ip_address=asset.ip_address, defaults={"nmap_asset": asset, "hostname": asset.hostname})
        string_json = str(asset.json_data)
        assetjson = json.loads(string_json)
        tcp_data = assetjson.get("tcp", {})
        for port_str, port_info in tcp_data.items():
            record = {
                "service": port_info.get("name"),
                "product": port_info.get("product") or None,
                "version": port_info.get("version") or None,
                "extrainfo": port_info.get("extrainfo") or None,
                "cpe": port_info.get("cpe") or None
            }
            ComputeAssetsNetworkPorts.objects.update_or_create(
                asset=computeasset,
                port_number=int(port_str),
                defaults={
                    **record,
                    "detection_severity": 1, # Default to 'Negligible'
                },
            )

def gather_mlnids_assets_info():
    networkflows = NetworkFlow.objects.all()
    for mlnids in networkflows:
        if mlnids.rf_prediction != "Benign":
            rf_confidence_level = round(mlnids.rf_confidence * 100)
        else:
            rf_confidence_level = 0
            
        if_confidence_level = round(mlnids.if_anomaly_score * -100)
        confidence_level = (rf_confidence_level + if_confidence_level) / 2
        calculate_confidence_level = round((confidence_level - 1) * 4 / 99 + 1)
        if is_internal_ip(mlnids.src_ip):
            computeassets, flag = ComputeAssets.objects.get_or_create(ip_address=mlnids.src_ip)
            ComputeAssetsNetworkDetection.objects.get_or_create(
                mlnids_detection=mlnids,
                detection_severity=calculate_confidence_level,
                compute_assets=computeassets,
            )
        if is_internal_ip(mlnids.dst_ip):
            computeassets, flag = ComputeAssets.objects.get_or_create(ip_address=mlnids.dst_ip)
            ComputeAssetsNetworkDetection.objects.get_or_create(
                mlnids_detection=mlnids,
                detection_severity=calculate_confidence_level,
                compute_assets=computeassets,
            )

def gather_assets_cve_infos():
    computeassets = ComputeAssets.objects.all()
    for asset in computeassets:
        network_ports = ComputeAssetsNetworkPorts.objects.filter(asset=asset)
        for port in network_ports:
            cves = []
            type, vendor, product, version, update, edition, language = parse_cpe_info(port.cpe)
            if type == None and vendor == None and product == None and version == None and update == None and edition == None and language == None:
                continue
            query = Q()

            if product is not None:
                query |= Q(cve_id__icontains=product)
                query |= Q(source_identifier__icontains=product)
                query |= Q(vuln_status__icontains=product)
                query |= Q(descriptions__icontains=product)
                query |= Q(metrics__icontains=product)
                query |= Q(weaknesses__icontains=product)
                query |= Q(references__icontains=product)

            if port.product is not None:
                query |= Q(cve_id__icontains=port.product)
                query |= Q(source_identifier__icontains=port.product)
                query |= Q(vuln_status__icontains=port.product)
                query |= Q(descriptions__icontains=port.product)
                query |= Q(metrics__icontains=port.product)
                query |= Q(weaknesses__icontains=port.product)
                query |= Q(references__icontains=port.product)
            
            cves = CveItem.objects.filter(query).order_by('-cve_id')

            for cve in cves:
                ComputeAssetsCVE.objects.get_or_create(compute_assets=asset, cve=cve)
 
def gather_all():
    gather_nmap_assets_infos()
    gather_mlnids_assets_info()
    gather_assets_cve_infos()

