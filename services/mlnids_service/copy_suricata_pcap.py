import glob, os, time

def is_file_old_enough(file_path, minutes):
    """Check if the file's last write time is older than the specified number of minutes."""
    try:
        file_last_modified_time = os.path.getmtime(file_path)  # Get the last modified time
        current_time = time.time()  # Current time in seconds since epoch
        time_difference = current_time - file_last_modified_time  # Time difference in seconds
        return time_difference >= minutes * 60  # Convert minutes to seconds
    except Exception as e:
        print(f"Error checking file age: {e}")
        return False

def copy_suricata_pcap(source_file, remote_file):
    if os.path.isfile(source_file):
        os.rename(source_file, remote_file)
        return True
    else:
        return False


def main():
    # Define the source folder and file pattern
    source_folder = "/path/to/source/folder"
    file_pattern = "log.pcap.*"  # File pattern for matching
    remote_directory = "analyse/pcap/todo"

    while True:
        # Find all files matching the pattern
        files_to_upload = glob.glob(os.path.join(source_folder, file_pattern))
    
        if not files_to_upload:
            print("No files matching the pattern were found.")
            return
    
        for file_path in files_to_upload:
            if is_file_old_enough(file_path, 30):
                print(f"File {file_path} is older than 30 minutes. Proceeding with upload.")
                
                file_name = os.path.basename(file_path)
                remote_file = os.path.join(remote_directory, file_name)

                # Upload the file via SCP
                if copy_suricata_pcap(file_path, remote_file):
                    print(f"File Successfully copied")
                else:
                    print(f"Failed to copy {file_path}. Skipping deletion.")
            else:
                print(f"File {file_path} does not match the required size of 1024 MB. Skipping.")

if __name__ == "__main__":
    main()