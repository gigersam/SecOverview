import sys
import os
import time
import statistics
import collections
import traceback
import math
import csv
import tempfile
from multiprocessing import Pool, current_process, Lock
import pandas as pd # Still used for structure definition convenience
import numpy as np

# --- Scapy Import ---
try:
    from scapy.all import IP, TCP, UDP, ICMP, Ether, PcapReader, Packet, conf
    # Suppress Scapy warnings (optional, can be noisy)
    conf.verb = 0
    SCAPY_AVAILABLE = True
except ImportError:
    print("ERROR: Scapy library not found. Please install it: pip install scapy")
    SCAPY_AVAILABLE = False
    # Define dummy classes if scapy is not available to avoid NameErrors later,
    # although the script will exit if SCAPY_AVAILABLE is False.
    class IP: pass
    class TCP: pass
    class UDP: pass
    class ICMP: pass
    class PcapReader: pass

# --- Flow and Feature Calculation Logic ---

def flow_default():
    # Stores minimal info per packet to conserve memory
    return {
        'packet_times_lens_flags_dirs': [], # Store tuples: (ts, len, flags_dict, direction, hdr_len, win)
        'flow_start_ts': None,
        'flow_last_ts': None,
        'src_ip': None,
        'dst_ip': None,
        'src_port': None,
        'dst_port': None,
        'protocol': None,
        'init_win_bytes_fwd': -1,
        'init_win_bytes_bwd': -1,
        'active': True, # Flag to manage flow timeout during processing
    }

def get_tcp_flags(pkt):
    """Extracts TCP flags into a dictionary."""
    flags = {}
    if TCP in pkt:
        try:
            flag_vals = pkt[TCP].flags
            flags['FIN'] = int(flag_vals & 0x01)
            flags['SYN'] = int(flag_vals & 0x02)
            flags['RST'] = int(flag_vals & 0x04)
            flags['PSH'] = int(flag_vals & 0x08)
            flags['ACK'] = int(flag_vals & 0x10)
            flags['URG'] = int(flag_vals & 0x20)
            # flags['ECE'] = int(flag_vals & 0x40) # Optional
            # flags['CWR'] = int(flag_vals & 0x80) # Optional
        except AttributeError: # Handle cases where flags might be missing/malformed
            pass
    return flags

def calculate_stats(data_list):
    """Safely calculates min, max, mean, stddev."""
    if not data_list: return 0.0, 0.0, 0.0, 0.0 # Return float zeros
    len_data = len(data_list)
    if len_data == 1:
        val = float(data_list[0])
        return val, val, val, 0.0

    try:
        # Ensure data are floats for calculations
        float_data = [float(x) for x in data_list]
        min_val = min(float_data)
        max_val = max(float_data)
        mean_val = statistics.mean(float_data)
        std_val = statistics.stdev(float_data) if len_data > 1 else 0.0
    except (statistics.StatisticsError, TypeError, ValueError) as e:
        # Handle potential errors if data isn't numeric or other stats issues
        # print(f"Debug: Stat calculation error - {e}, Data: {data_list[:10]}...") # Uncomment for debugging
        return 0.0, 0.0, 0.0, 0.0
    except Exception as e: # Catch any other unexpected math errors
        # print(f"Debug: Unexpected Stat calculation error - {e}") # Uncomment for debugging
        return 0.0, 0.0, 0.0, 0.0

    return min_val, max_val, mean_val, std_val

def calculate_inter_arrival_times(timestamps):
    """Calculates inter-arrival times from a list of timestamps."""
    if len(timestamps) < 2: return []
    timestamps.sort() # Ensure order
    iats = [(timestamps[i] - timestamps[i-1]) for i in range(1, len(timestamps))]
    # Filter out potential negative IATs if timestamps were unordered or had issues
    # Also filter out excessively large IATs if necessary (e.g., > timeout value?)
    # return [max(0.0, iat) for iat in iats] # Ensure non-negative
    return [float(iat) for iat in iats if iat >= 0]


def calculate_flow_features(flow_data, flow_key):
    """Calculates aggregate features for a single completed flow."""
    if not flow_data['packet_times_lens_flags_dirs']:
        return None # Ignore empty flows

    features = {}
    try:
        # Basic Info
        features['flow_key'] = "_".join(map(str, flow_key))
        features['src_ip'] = flow_data['src_ip']
        features['dst_ip'] = flow_data['dst_ip']
        features['src_port'] = flow_data['src_port']
        features['dst_port'] = flow_data['dst_port']
        features['protocol'] = flow_data['protocol']

        # Extract lists from stored tuples
        packets_info = flow_data['packet_times_lens_flags_dirs']
        timestamps = [p[0] for p in packets_info]
        lengths = [p[1] for p in packets_info]
        flags_list = [p[2] for p in packets_info]
        directions = [p[3] for p in packets_info]
        hdr_lens = [p[4] for p in packets_info]
        # windows = [p[5] for p in packets_info] # Not used beyond init_win currently

        # Timestamps and Duration
        features['flow_start_ts'] = flow_data['flow_start_ts']
        features['flow_last_ts'] = flow_data['flow_last_ts']
        duration = features['flow_last_ts'] - features['flow_start_ts']
        # Use max(duration, small_value) to avoid division by zero later
        # A very small positive value is better than 0 for rates.
        features['flow_duration'] = max(duration, 1e-9)

        # Packet and Byte Counts by direction
        fwd_indices = [i for i, d in enumerate(directions) if d == 'fwd']
        bwd_indices = [i for i, d in enumerate(directions) if d == 'bwd']

        fwd_pkts_tot = len(fwd_indices)
        bwd_pkts_tot = len(bwd_indices)
        tot_pkts = fwd_pkts_tot + bwd_pkts_tot
        features['fwd_pkts_tot'] = fwd_pkts_tot
        features['bwd_pkts_tot'] = bwd_pkts_tot
        features['tot_pkts'] = tot_pkts

        if tot_pkts == 0: return None # Should not happen if packets_info isn't empty, but safety

        fwd_bytes_tot = sum(lengths[i] for i in fwd_indices)
        bwd_bytes_tot = sum(lengths[i] for i in bwd_indices)
        tot_bytes = fwd_bytes_tot + bwd_bytes_tot
        features['fwd_bytes_tot'] = fwd_bytes_tot
        features['bwd_bytes_tot'] = bwd_bytes_tot
        features['tot_bytes'] = tot_bytes

        # Packet Length Stats by direction
        fwd_pkt_lengths = [lengths[i] for i in fwd_indices]
        bwd_pkt_lengths = [lengths[i] for i in bwd_indices]
        features['fwd_pkt_len_min'], features['fwd_pkt_len_max'], features['fwd_pkt_len_mean'], features['fwd_pkt_len_std'] = calculate_stats(fwd_pkt_lengths)
        features['bwd_pkt_len_min'], features['bwd_pkt_len_max'], features['bwd_pkt_len_mean'], features['bwd_pkt_len_std'] = calculate_stats(bwd_pkt_lengths)
        features['flow_pkt_len_min'], features['flow_pkt_len_max'], features['flow_pkt_len_mean'], features['flow_pkt_len_std'] = calculate_stats(lengths)
        features['avg_pkt_size'] = features['flow_pkt_len_mean']

        # Inter-Arrival Time (IAT) Stats
        fwd_timestamps = sorted([timestamps[i] for i in fwd_indices])
        bwd_timestamps = sorted([timestamps[i] for i in bwd_indices])
        flow_timestamps_sorted = sorted(timestamps)

        fwd_iats = calculate_inter_arrival_times(fwd_timestamps)
        bwd_iats = calculate_inter_arrival_times(bwd_timestamps)
        flow_iats = calculate_inter_arrival_times(flow_timestamps_sorted)

        features['fwd_iat_min'], features['fwd_iat_max'], features['fwd_iat_mean'], features['fwd_iat_std'] = calculate_stats(fwd_iats)
        features['bwd_iat_min'], features['bwd_iat_max'], features['bwd_iat_mean'], features['bwd_iat_std'] = calculate_stats(bwd_iats)
        features['flow_iat_min'], features['flow_iat_max'], features['flow_iat_mean'], features['flow_iat_std'] = calculate_stats(flow_iats)

        # Header Lengths and Segment Size
        fwd_header_bytes = sum(hdr_lens[i] for i in fwd_indices)
        bwd_header_bytes = sum(hdr_lens[i] for i in bwd_indices)
        features['fwd_header_len'] = fwd_header_bytes
        features['bwd_header_len'] = bwd_header_bytes

        # Ensure payload bytes are not negative if header length exceeds packet length (malformed?)
        fwd_payload_bytes = max(0, fwd_bytes_tot - fwd_header_bytes)
        bwd_payload_bytes = max(0, bwd_bytes_tot - bwd_header_bytes)
        features['fwd_seg_size_avg'] = (fwd_payload_bytes / fwd_pkts_tot) if fwd_pkts_tot > 0 else 0.0
        features['bwd_seg_size_avg'] = (bwd_payload_bytes / bwd_pkts_tot) if bwd_pkts_tot > 0 else 0.0

        # Rates
        flow_duration_safe = features['flow_duration'] # Already adjusted to be > 0
        features['pkts_per_sec'] = tot_pkts / flow_duration_safe
        features['bytes_per_sec'] = tot_bytes / flow_duration_safe

        # TCP Flags Counts
        fwd_flags_agg = collections.defaultdict(int)
        bwd_flags_agg = collections.defaultdict(int)
        tot_flags_agg = collections.defaultdict(int)

        for i, flags in enumerate(flags_list):
            direction = directions[i]
            for flag, present in flags.items():
                if present:
                    tot_flags_agg[flag] += 1
                    if direction == 'fwd':
                        fwd_flags_agg[flag] += 1
                    else: # 'bwd'
                        bwd_flags_agg[flag] += 1

        features['fwd_PSH_flags'] = fwd_flags_agg['PSH']
        features['bwd_PSH_flags'] = bwd_flags_agg['PSH']
        features['fwd_URG_flags'] = fwd_flags_agg['URG']
        features['bwd_URG_flags'] = bwd_flags_agg['URG']
        features['SYN_flag_cnt'] = tot_flags_agg['SYN']
        features['FIN_flag_cnt'] = tot_flags_agg['FIN']
        features['RST_flag_cnt'] = tot_flags_agg['RST']
        features['ACK_flag_cnt'] = tot_flags_agg['ACK']
        features['PSH_flag_cnt'] = tot_flags_agg['PSH'] # Total PSH
        features['URG_flag_cnt'] = tot_flags_agg['URG'] # Total URG

        # Download/Upload Ratio
        # Add small epsilon to denominator to prevent division by zero if fwd_bytes_tot is 0
        features['down_up_ratio'] = bwd_bytes_tot / (fwd_bytes_tot + 1e-9)

        # Initial Window Sizes
        features['init_win_bytes_fwd'] = flow_data['init_win_bytes_fwd']
        features['init_win_bytes_bwd'] = flow_data['init_win_bytes_bwd']

        # Final check for NaN/inf introduced by calculations (rates, stddevs, ratios)
        for key, value in features.items():
            # Check only numeric types susceptible to these issues
            if isinstance(value, (float, np.floating, int, np.integer)):
                # Check if value is NaN or +/- Infinity
                is_nan = math.isnan(float(value)) if isinstance(value, (float, np.floating)) else False
                is_inf = math.isinf(float(value)) if isinstance(value, (float, np.floating)) else False

                if is_nan or is_inf:
                    features[key] = 0.0 # Replace NaN/Inf with 0.0
                # Optional: Check for excessively large values if needed
                # elif abs(value) > 1e18: # Example threshold
                #    features[key] = 0.0 # Or clip to a max value

    except Exception as calc_err:
        print(f"Error calculating features for flow {flow_key}: {calc_err}")
        traceback.print_exc() # Print detailed traceback for debugging
        return None # Return None if feature calculation fails

    return features


# --- Feature Definitions (Used for header row) ---
# Define the column order based on the calculate_flow_features function output keys
# Ensure this list matches the keys returned by calculate_flow_features
FEATURE_COLUMNS = [
    'flow_key', 'src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol',
    'flow_start_ts', 'flow_last_ts', 'flow_duration',
    'fwd_pkts_tot', 'bwd_pkts_tot', 'tot_pkts',
    'fwd_bytes_tot', 'bwd_bytes_tot', 'tot_bytes',
    'fwd_pkt_len_min', 'fwd_pkt_len_max', 'fwd_pkt_len_mean', 'fwd_pkt_len_std',
    'bwd_pkt_len_min', 'bwd_pkt_len_max', 'bwd_pkt_len_mean', 'bwd_pkt_len_std',
    'flow_pkt_len_min', 'flow_pkt_len_max', 'flow_pkt_len_mean', 'flow_pkt_len_std',
    'avg_pkt_size',
    'fwd_iat_min', 'fwd_iat_max', 'fwd_iat_mean', 'fwd_iat_std',
    'bwd_iat_min', 'bwd_iat_max', 'bwd_iat_mean', 'bwd_iat_std',
    'flow_iat_min', 'flow_iat_max', 'flow_iat_mean', 'flow_iat_std',
    'fwd_header_len', 'bwd_header_len',
    'fwd_seg_size_avg', 'bwd_seg_size_avg',
    'pkts_per_sec', 'bytes_per_sec',
    'fwd_PSH_flags', 'bwd_PSH_flags', 'fwd_URG_flags', 'bwd_URG_flags',
    'SYN_flag_cnt', 'FIN_flag_cnt', 'RST_flag_cnt', 'ACK_flag_cnt',
    'PSH_flag_cnt', 'URG_flag_cnt',
    'down_up_ratio',
    'init_win_bytes_fwd', 'init_win_bytes_bwd'
]


# --- PCAP Processing Function (Worker - Writes to Temp File) ---

def process_pcap_to_temp_file(pcap_filepath, temp_file_path, flow_timeout=60.0, cleanup_interval=5000):
    """
    Processes a single PCAP file and writes flow features directly to a temp CSV file.

    Args:
        pcap_filepath (str): Path to the PCAP file.
        temp_file_path (str): Path to the temporary CSV file to write to.
        flow_timeout (float): Inactivity timeout in seconds.
        cleanup_interval (int): How often (in packets) to check for timed-out flows.

    Returns:
        tuple: (bool, str, int): Success status, temp file path, number of flows written.
    """
    process_name = current_process().name
    print(f"[{process_name}] Processing: {os.path.basename(pcap_filepath)} -> {os.path.basename(temp_file_path)}")
    start_time = time.time()

    if not SCAPY_AVAILABLE:
        print(f"[{process_name}] Error: Scapy is not available.")
        return False, temp_file_path, 0

    flows = collections.defaultdict(flow_default)
    packet_count = 0
    flows_written = 0
    writer = None
    temp_file = None

    try:
        # Open the temporary file for writing
        temp_file = open(temp_file_path, 'w', newline='', encoding='utf-8')
        writer = csv.DictWriter(temp_file, fieldnames=FEATURE_COLUMNS, extrasaction='ignore')
        # 'extrasaction=ignore' prevents errors if calculate_flow_features accidentally returns an extra key
        writer.writeheader() # Write header ONLY to the temp file

        # Use PcapReader for memory efficiency with large files
        with PcapReader(pcap_filepath) as pcap_reader:
            for pkt_num, pkt in enumerate(pcap_reader):
                packet_count += 1

                # --- Packet Parsing and Flow Logic ---
                if not pkt.haslayer(IP): continue
                ip_layer = pkt[IP]
                # Optionally filter IPv6 if needed: if ip_layer.version != 4: continue

                try:
                    pkt_time = float(pkt.time)
                    src_ip = ip_layer.src; dst_ip = ip_layer.dst; proto = ip_layer.proto
                    pkt_len = ip_layer.len # Use IP total length (header + payload)
                    hdr_len = ip_layer.ihl * 4 # IP Header length in bytes
                    tcp_flags = {}; udp_len = 0; tcp_win = -1; src_port = 0; dst_port = 0

                    if proto == 6 and TCP in pkt: # TCP
                        tcp_layer = pkt[TCP]
                        src_port = tcp_layer.sport; dst_port = tcp_layer.dport
                        tcp_flags = get_tcp_flags(pkt)
                        hdr_len += tcp_layer.dataofs * 4 # TCP Header length
                        tcp_win = tcp_layer.window
                    elif proto == 17 and UDP in pkt: # UDP
                        udp_layer = pkt[UDP]
                        src_port = udp_layer.sport; dst_port = udp_layer.dport
                        hdr_len += 8 # Fixed UDP header size
                        udp_len = udp_layer.len # UDP length (header + data)
                    elif proto == 1 and ICMP in pkt: # ICMP
                         # Assign ports 0 for ICMP, or use type/code if desired
                         src_port, dst_port = 0, 0
                         hdr_len += 8 # Common ICMP header size (can vary slightly)
                    else:
                        continue # Skip other L4 protocols or packets without L4 info

                except Exception as parse_err:
                    # print(f"[{process_name}] Warning: Error parsing packet #{packet_count} in {os.path.basename(pcap_filepath)}. Skipping. Error: {parse_err}")
                    continue # Skip malformed packets

                # --- Flow Identification (consistent key) ---
                flow_key_part1 = tuple(sorted((src_ip, dst_ip)))
                flow_key_part2 = tuple(sorted((src_port, dst_port)))
                flow_key = flow_key_part1 + flow_key_part2 + (proto,)

                # --- Add packet to flow / Update flow state ---
                flow = flows[flow_key]

                # Initialize flow metadata on first packet
                if not flow['packet_times_lens_flags_dirs']:
                    flow['flow_start_ts'] = pkt_time
                    flow['src_ip'] = src_ip # Capture the 'initiator' based on first packet seen
                    flow['dst_ip'] = dst_ip
                    flow['src_port'] = src_port
                    flow['dst_port'] = dst_port
                    flow['protocol'] = proto

                # Update last seen time and mark active
                flow['flow_last_ts'] = pkt_time
                flow['active'] = True

                # Determine packet direction relative to the first packet seen for this key
                is_forward = (src_ip == flow['src_ip'] and dst_ip == flow['dst_ip'] and
                              src_port == flow['src_port'] and dst_port == flow['dst_port'])
                direction = 'fwd' if is_forward else 'bwd'

                # Append essential packet info (Timestamp, Length, TCP Flags, Direction, Header Length, TCP Window)
                flow['packet_times_lens_flags_dirs'].append(
                    (pkt_time, pkt_len, tcp_flags, direction, hdr_len, tcp_win)
                )

                # Capture Initial Window Sizes (more robustly for TCP)
                if proto == 6: # Only for TCP
                    is_syn = tcp_flags.get('SYN', 0) == 1
                    # is_ack = tcp_flags.get('ACK', 0) == 1 # Might be needed for SYN-ACK logic
                    if is_forward:
                         if flow['init_win_bytes_fwd'] == -1 and is_syn:
                            flow['init_win_bytes_fwd'] = tcp_win
                    else: # Backward direction packet
                         # Captures SYN-ACK or SYN in reverse direction (simultaneous open)
                         if flow['init_win_bytes_bwd'] == -1 and is_syn:
                             flow['init_win_bytes_bwd'] = tcp_win
                # --- End Packet Logic ---


                # --- Periodic Flow Timeout Check and Write to Temp File ---
                if packet_count % cleanup_interval == 0:
                    # print(f"[{process_name}] Packet {packet_count}, checking timeouts (active flows: {len(flows)})...")
                    keys_to_delete = []
                    # Iterate over a copy of items for safe dictionary modification
                    for f_key, f_data in list(flows.items()):
                        # Check if flow is marked active and if timeout has exceeded
                        if f_data['active'] and (pkt_time - f_data['flow_last_ts']) > flow_timeout:
                            processed_flow = calculate_flow_features(f_data, f_key)
                            if processed_flow:
                                try:
                                    # Ensure calculated features are in the correct order/subset for DictWriter
                                    writer.writerow(processed_flow)
                                    flows_written += 1
                                except Exception as write_err:
                                     print(f"[{process_name}] Error writing flow {f_key} to temp file '{os.path.basename(temp_file_path)}': {write_err}")
                            keys_to_delete.append(f_key) # Mark flow for deletion
                        # Optimization: Mark flow as inactive if idle for half the timeout period
                        # This reduces checks on subsequent iterations if it remains idle.
                        elif f_data['active'] and (pkt_time - f_data['flow_last_ts']) > (flow_timeout / 2):
                             f_data['active'] = False

                    # Delete timed-out flows from memory
                    for key in keys_to_delete:
                        try:
                            del flows[key]
                        except KeyError:
                            pass # Ignore if already deleted


        # --- Process and Write Remaining Flows After Reading PCAP ---
        print(f"[{process_name}] Finished reading {packet_count} packets. Writing remaining {len(flows)} flows...")
        remaining_keys = list(flows.keys()) # Get keys before iterating
        for f_key in remaining_keys:
            f_data = flows[f_key]
            processed_flow = calculate_flow_features(f_data, f_key)
            if processed_flow:
                 try:
                     writer.writerow(processed_flow)
                     flows_written += 1
                 except Exception as write_err:
                     print(f"[{process_name}] Error writing final flow {f_key} to temp file '{os.path.basename(temp_file_path)}': {write_err}")
            # Clean up the flow from memory after processing
            try:
                 del flows[f_key]
            except KeyError:
                 pass


        end_time = time.time()
        duration = end_time - start_time
        print(f"[{process_name}] Completed {os.path.basename(pcap_filepath)} in {duration:.2f}s. Wrote {flows_written} flows to {os.path.basename(temp_file_path)}.")
        return True, temp_file_path, flows_written

    except FileNotFoundError:
        print(f"[{process_name}] Error: File not found: {pcap_filepath}")
        return False, temp_file_path, 0
    except Exception as e:
        print(f"[{process_name}] Unhandled Error processing {os.path.basename(pcap_filepath)}: {e}")
        print(f"[{process_name}] Traceback:")
        traceback.print_exc() # Print detailed traceback for debugging
        return False, temp_file_path, 0
    finally:
        # Ensure the temporary file is closed properly
        if temp_file and not temp_file.closed:
            temp_file.close()


# --- File Merging Function ---
def merge_temporary_files(temp_files, output_csv_path, header):
    """
    Merges temporary CSV files into a single output CSV file, handling headers.

    Args:
        temp_files (list): List of paths to temporary CSV files that succeeded.
        output_csv_path (str): Path to the final output CSV file.
        header (list): List of column names for the header.
    """
    if not temp_files:
        print("No temporary files provided for merging.")
        return 0 # Return 0 rows written

    print(f"\nMerging {len(temp_files)} temporary files into {output_csv_path}...")
    start_merge_time = time.time()
    total_rows_written = 0
    files_merged_count = 0

    #if not os.path.exists(output_csv_path):
    #    with open(output_csv_path, 'w') as f:
    #        pass  # creates an empty file

    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header) # Write header ONCE to the final file

            for i, temp_file in enumerate(temp_files):
                print(f"  Merging file {i+1}/{len(temp_files)}: {os.path.basename(temp_file)}")
                rows_in_file = 0
                try:
                    # Check if file exists and is not empty before trying to read
                    if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                        with open(temp_file, 'r', newline='', encoding='utf-8') as infile:
                            reader = csv.reader(infile)
                            try:
                                next(reader) # Skip header row of the temporary file
                                for row in reader:
                                    writer.writerow(row)
                                    rows_in_file += 1
                            except StopIteration:
                                print(f"    Warning: Temporary file {os.path.basename(temp_file)} contained only a header. Skipping content.")
                            except Exception as read_err:
                                print(f"    Error reading content from {os.path.basename(temp_file)}: {read_err}. Skipping content.")
                        total_rows_written += rows_in_file
                        files_merged_count += 1
                        print(f"    -> Merged {rows_in_file} rows.")
                    else:
                         print(f"    Warning: Temporary file {os.path.basename(temp_file)} not found or is empty. Skipping.")

                except Exception as merge_err:
                     print(f"    Error processing temporary file {os.path.basename(temp_file)}: {merge_err}. Skipping.")

    except Exception as e:
        print(f"Fatal Error during final file merge process: {e}")
        traceback.print_exc()
        # Don't clean up temps automatically if merge fails badly, user might need them
        return -1 # Indicate merge failure

    finally:
        # Clean up temporary files AFTER successful merge attempt (or if merge failed gracefully)
        print("\nCleaning up temporary files...")
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    # print(f"  Removed: {os.path.basename(temp_file)}")
            except OSError as e:
                print(f"  Warning: Could not remove temporary file {os.path.basename(temp_file)}: {e}")

    end_merge_time = time.time()
    print(f"Merging of {files_merged_count} files complete in {end_merge_time - start_merge_time:.2f} seconds.")
    print(f"Total flows written to final file: {total_rows_written}")
    return total_rows_written


# --- Main Execution Logic ---
if __name__ == "__main__":
    if not SCAPY_AVAILABLE:
        sys.exit(1) # Exit if Scapy isn't installed

    if len(sys.argv) != 3:
        print("\nUsage: python pcap_feature_extractor_lowmem.py <input_pcap_directory> <output_csv_file>\n")
        print("  <input_pcap_directory>: Path to the folder containing .pcap or .pcapng files.")
        print("  <output_csv_file>: Path to save the combined features CSV file.")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_csv = sys.argv[2]
    # Use a dedicated subdirectory in the system temp dir for our temp files
    temp_dir_base = os.path.join(tempfile.gettempdir(), f"pcap_features_temp_{os.getpid()}")
    os.makedirs(temp_dir_base, exist_ok=True)
    print(f"Using temporary directory: {temp_dir_base}")


    # --- Validate Input Directory ---
    if not os.path.isdir(input_dir):
        print(f"Error: Input path '{input_dir}' is not a valid directory.")
        sys.exit(1)

    # --- Find PCAP Files ---
    pcap_files = []
    print(f"Searching for .pcap or .pcapng files in: {input_dir}")
    try:
        for filename in os.listdir(input_dir):
            if filename.lower().endswith(('.pcap', '.pcapng', '_processed')):
                pcap_files.append(os.path.join(input_dir, filename))
    except Exception as e:
        print(f"Error accessing directory '{input_dir}': {e}")
        sys.exit(1)

    if not pcap_files:
        print("No .pcap or .pcapng files found in the specified directory.")
        sys.exit(0) # Not an error, just nothing to do

    print(f"Found {len(pcap_files)} PCAP files to process.")

    # --- Parameters for Low Memory ---
    # Shorter timeout flushes flows faster; more frequent cleanup checks more often
    FLOW_TIMEOUT_SECONDS = 30.0 # Shorter timeout (e.g., 30-60 seconds)
    CLEANUP_PACKET_INTERVAL = 2500 # More frequent cleanup (e.g., every 2500-5000 packets)

    # --- Setup Multiprocessing ---
    # Use slightly fewer processes than cores if possible
    num_processes = max(1, os.cpu_count() - 1 if os.cpu_count() else 1)
    # Can override with environment variable for testing: num_processes = int(os.environ.get("NUM_PROC", num_processes))
    print(f"Initializing multiprocessing pool with {num_processes} workers...")

    tasks = []
    temp_file_paths_generated = []
    # Create tasks with unique temporary file paths for each worker
    for i, pcap_file in enumerate(pcap_files):
        # Create a unique temporary file name
        temp_filename = f"pcap_features_{os.path.basename(pcap_file)}_{i}.csv.tmp"
        temp_path = os.path.join(temp_dir_base, temp_filename)
        temp_file_paths_generated.append(temp_path)
        tasks.append((pcap_file, temp_path, FLOW_TIMEOUT_SECONDS, CLEANUP_PACKET_INTERVAL))

    worker_results = []
    start_multi_time = time.time()

    try:
        # Use 'with Pool(...)' for automatic resource management
        with Pool(processes=num_processes) as pool:
            # Use starmap to pass multiple arguments from 'tasks' to the worker function
            worker_results = pool.starmap(process_pcap_to_temp_file, tasks)

    except Exception as e:
        print(f"\nAn critical error occurred during multiprocessing pool execution: {e}")
        traceback.print_exc()
        # Worker_results might be incomplete here
    finally:
        # Ensure pool is closed if 'with' statement was interrupted
        # (The 'with' statement handles this, but good practice in complex scenarios)
        pass

    total_multi_duration = time.time() - start_multi_time
    print(f"\nMultiprocessing pool phase finished in {total_multi_duration:.2f} seconds.")

    # --- Collect Successful Temp Files and Merge ---
    successful_temp_files = []
    failed_files_count = 0
    total_flows_extracted = 0

    for result in worker_results:
        if result is not None:
            success, temp_path, flow_count = result
            if success:
                successful_temp_files.append(temp_path)
                total_flows_extracted += flow_count
            else:
                failed_files_count += 1
        else:
            # This case indicates a potential unhandled exception or issue in the worker/pool
            failed_files_count += 1


    print(f"\nSummary from workers: {len(successful_temp_files)} succeeded, {failed_files_count} failed.")
    print(f"Total flows extracted by workers: {total_flows_extracted}")

    merge_succeeded = False
    if successful_temp_files:
        try:
             merge_result = merge_temporary_files(successful_temp_files, output_csv, FEATURE_COLUMNS)
             if merge_result >= 0: # Check if merge function indicated success (non-negative rows)
                  print(f"\nMerge successful. Final output saved to: {output_csv}")
                  merge_succeeded = True
             else:
                  print("\nMerge process reported an error. Final file might be incomplete or corrupted.")
        except Exception as final_merge_err:
            print(f"\nError during final merge execution: {final_merge_err}")
            traceback.print_exc()
    else:
        print("\nNo successful temporary files to merge. No output file created.")

    # Optional: Clean up the base temporary directory if merge was successful
    if merge_succeeded:
        try:
            # Check again if directory exists before removing
            if os.path.exists(temp_dir_base):
                # Be cautious with rmtree; ensure it's the correct directory
                import shutil
                shutil.rmtree(temp_dir_base)
                print(f"Removed temporary directory: {temp_dir_base}")
        except Exception as cleanup_err:
            print(f"Warning: Could not remove temporary directory {temp_dir_base}: {cleanup_err}")
    else:
        print(f"Merge did not complete successfully. Temporary files might remain in: {temp_dir_base}")


    print("\nProcessing finished.")
    # Note: total execution time would need a global start time before multiprocessing starts