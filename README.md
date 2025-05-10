# Project SecOverview 
This repository contains a small hobby project designed to help check my system for unknown assets or open ports.

## Apps
The project currently contains the following apps:
- NMAP Scanner: A simple WebUI to execute NMAP scans and store the detected results.
- IP Check: A simple WebUI to check IP ASN data.
- DNS Record Check: A simple WebUI to check a domain's DNS records.
- RSS Reader: Displays the latest news from various sources.
- YARA Rules Checker: A WebUI to upload files which will be checked against some YARA rules.
- MLNIDS Detection: A WebUI to display detected anomalies in the captured network flow.
- Assets: The Assets view gathers all stored data from the apps, correlates them, and displays them from the asset perspective.

## Installation
The installation of SecOverview was tested on Debian 12. Due to the chat feature, some CPU/GPU power is required. It is also possible to run the Ollama instance on a different host. For the MLNIDS Detection feature, a GPU is highly recommended. It can also be run on a different host. The MLNIDS feature analyses captured network traffic in the PCAP format. To get PCAPs, a tool like Suricata is recommended.

To install SecOverview the easy way, there is an install script available:
- [SecOverview install.sh](https://raw.githubusercontent.com/gigersam/SecOverview/refs/heads/main/install.sh)

After downloading, enable the file to be executed:

```Bash Bash
chomd +x install.sh
```

The script will install the following components:
- python3
- python3-venv
- pyhton3-pip
- git
- nginx
- nmap 
- ollama 

Then run the script with sudo privileges:
```Bash Bash
sudo ./install.sh
```

After the successful installation, you can access it with a browser. The default URL is: http://localhost

If you have any questions or suggestions, please feel free to contact me at [samuelgiger.com](https://samuelgiger.com/contact/).