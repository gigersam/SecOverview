import os
import sys
import subprocess
import pandas as pd
import time
import datetime
import logging
import random
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TRAIN_SCRIPT = "train.py"
PROCESS_SCRIPT = "process.py"
CONVERT_PCAP_CSV = "convert_pcap_to_csv.py"
CSV_DONE = "analyse/csv/done"
CSV_TODO = "analyse/csv/todo/out.csv"
CSV_SUSPICIOUS_TODO = "analyse/suspicious/todo/"
CSV_SUSPICIOUS_DONE = "analyse/suspicious/done/"
CSV_TODO_PATH = "analyse/csv/todo"
CSV_CLASSIFIED_PATH = "analyse/processed_output/"
PCAP_DONE = "analyse/pcap/done/"
PCAP_TODO = "analyse/pcap/todo"
IF_DATASET = "datasets/if_training.csv"
IF_ANOMALY_SCORE = -0.75

# --- Helper Functions ---
def run_script(script_name, args_list):
    """Runs a python script as a subprocess."""
    command = ["python3", script_name] + args_list
    logging.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info(f"Script {script_name} output:\n{result.stdout}")
        if result.stderr:
            logging.warning(f"Script {script_name} errors:\n{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {script_name}: {e}")
        logging.error(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"Script {script_name} not found. Make sure it's in the same directory or path.")
        return False



# --- Main Simulation Loop ---
if __name__ == "__main__":
    os.makedirs(CSV_DONE, exist_ok=True)
    os.makedirs(PCAP_DONE, exist_ok=True)
    os.makedirs(PCAP_TODO, exist_ok=True)
    os.makedirs("models", exist_ok=True) # Ensure models dir exists
    logging.info(f"Analyser started.")
    while True:
        if os.listdir(PCAP_TODO):
            logging.info(f"Data files found in {PCAP_TODO}.")
            run_script(CONVERT_PCAP_CSV, [f"{PCAP_TODO}", f"{CSV_TODO}"])
            for file in os.listdir(PCAP_TODO):
                source_file = os.path.join(PCAP_TODO, file)
                now = datetime.datetime.now()
                name = formatted = now.strftime("%Y-%m-%d_%H_%M_%S")
                target_file = os.path.join(PCAP_DONE, (file + "_" + name))

                if os.path.isfile(source_file):
                    os.rename(source_file, target_file) 
        #else:
        #    logging.info(f"No data files found in {PCAP_TODO}")

        if os.path.exists(CSV_TODO):
            logging.info(f"Data files found in {PCAP_TODO}.")
            # List to store dataframes
            now = datetime.datetime.now()
            name = formatted = now.strftime("%Y-%m-%d_%H_%M_%S")
            run_script(PROCESS_SCRIPT, [f"{CSV_TODO}", f"{name}.csv"])
            final_df = pd.read_csv(IF_DATASET)

            # Append new CSVs directly to the existing dataframe
            temp_df = pd.read_csv(CSV_CLASSIFIED_PATH + name + ".csv")
            anomaly_data = []
            benign_data = []
            print(temp_df)
            for index, row in temp_df.iterrows():
                if row["rf_prediction"] != "Benign":
                    anomaly_data.append(row)
                elif row.get("if_anomaly_score") <= IF_ANOMALY_SCORE:
                    anomaly_data.append(row)
                else:
                    benign_data.append(row)
            
            if len(anomaly_data) > 0:
                print("Anomaly data found.")
                anomaly_df = pd.DataFrame(anomaly_data)
                anomaly_df.to_csv(CSV_SUSPICIOUS_TODO + name + ".csv", index=False)

                CREDENTIALS = {
                    "username": os.getenv('CREDENTIALSUSERNAME'),
                    "password": os.getenv('CREDENTIALSPASSWORD')
                }
                token_url = os.getenv('APISERVERURL') + "/api/token"
                response = requests.post(token_url, json=CREDENTIALS)
                access_token = response.json().get("access")
                headers = {"Authorization": f"Bearer {access_token}"}
    
                file_path = CSV_SUSPICIOUS_TODO + name + ".csv"
    
                url = os.getenv('APISERVERURL') + "/api/mlnids/upload"
                with open(file_path, 'rb') as f:
                    files = {'file': (file_path, f, 'text/csv')}
                    response = requests.post(url, files=files, headers=headers)
    
                source_file_suspicious = file_path
                target_file_suspicious  = os.path.join(CSV_SUSPICIOUS_DONE, name + ".csv")
    
                if os.path.isfile(source_file_suspicious):
                    os.rename(source_file_suspicious, target_file_suspicious)

            benign_df = pd.DataFrame(benign_data)

            final_df = pd.concat([final_df, benign_df], ignore_index=True)
            # Optionally save to a new CSV
            final_df.to_csv(IF_DATASET, index=False)

            source_file = CSV_TODO
            target_file = os.path.join(CSV_DONE, name + ".csv")

            if os.path.isfile(source_file):
                os.rename(source_file, target_file) 

            run_script(TRAIN_SCRIPT, [f"--train-if", f"--if-data={IF_DATASET}"])
        #else:
        #    logging.info(f"No data files found in {CSV_TODO}")
        
        time.sleep(1 * 60)

