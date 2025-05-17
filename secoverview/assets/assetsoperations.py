from nmapapp.models import NmapAssets, Nmapscan, AssetsNmapscan
from mlnids.models import NetworkFlow
from .models import *
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
            
def gather_all():
    gather_nmap_assets_infos()
    gather_mlnids_assets_info()
