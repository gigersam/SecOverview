import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
import joblib
import os
import argparse
import logging
import gc
import numpy as np
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Feature Definitions ---
# Represents ALL possible features needed by either RF or IF data
# Ensure consistency in naming (after stripping whitespace)
# User should replace this with their comprehensive feature list
DEFAULT_NUMERICAL_FEATURES = [
    "flow_duration", "fwd_pkts_tot", "bwd_pkts_tot",
    "fwd_bytes_tot", "bwd_bytes_tot", "fwd_pkt_len_min", "fwd_pkt_len_max",
    "fwd_pkt_len_mean", "fwd_pkt_len_std", "bwd_pkt_len_min", "bwd_pkt_len_max",
    "bwd_pkt_len_mean", "bwd_pkt_len_std", "flow_pkt_len_min", "flow_pkt_len_max",
    "flow_pkt_len_mean", "flow_pkt_len_std", "fwd_iat_min", "fwd_iat_max",
    "fwd_iat_mean", "fwd_iat_std", "bwd_iat_min", "bwd_iat_max",
    "bwd_iat_mean", "bwd_iat_std", "flow_iat_min", "flow_iat_max",
    "flow_iat_mean", "flow_iat_std", "fwd_header_len", "bwd_header_len",
    "pkts_per_sec", "bytes_per_sec", "down_up_ratio", "avg_pkt_size",
    "fwd_seg_size_avg", "bwd_seg_size_avg", "init_win_bytes_fwd",
    "init_win_bytes_bwd",
    "fwd_PSH_flags", "bwd_PSH_flags", "fwd_URG_flags", "bwd_URG_flags",
    "SYN_flag_cnt", "FIN_flag_cnt", "RST_flag_cnt", "ACK_flag_cnt",
    "PSH_flag_cnt", "URG_flag_cnt",
    "protocol", "dst_port"
]
DEFAULT_CATEGORICAL_FEATURES = [] # Explicitly empty if none are categorical by default
LABEL_COLUMN = 'Label' # Expected label column name for RF data

# --- Default Paths and Model Params ---
MODELS_DIR = "models"
# Path now points to the combined object (preprocessor + features)
PREPROCESSOR_OBJECT_PATH = os.path.join(MODELS_DIR, "preprocessor_and_features.joblib")
RF_MODEL_PATH = os.path.join(MODELS_DIR, "rf_model.joblib")
IF_MODEL_PATH = os.path.join(MODELS_DIR, "if_model.joblib")

DEFAULT_CHUNK_SIZE = 2000000
DEFAULT_TARGET_SAMPLE_SIZE = 16233002 # Sample size from the RF/main data path
DEFAULT_N_ESTIMATORS = 100
DEFAULT_MAX_DEPTH = 50
DEFAULT_N_JOBS = 3

# --- Memory Optimization Function ---
def optimize_dtypes(df):
    """Attempts to downcast numerical columns to smaller types."""
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
    return df

# --- Preprocessor Building Function (Including Imputation) ---
def build_preprocessor(numerical_features, categorical_features, known_categories):
    """Builds a ColumnTransformer including imputation for numerical features."""
    transformers = []
    if numerical_features:
        numeric_pipeline = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')), # Handle NaNs/Infs replaced by NaN
            ('scaler', StandardScaler())
        ])
        transformers.append(('num', numeric_pipeline, numerical_features))
        logging.info(f"Preprocessor: Applying Imputer(median) + StandardScaler to: {numerical_features}")

    if categorical_features:
        # OHE Pipeline (can add imputer here too if needed for categorical NaNs)
        categorical_pipeline = Pipeline(steps=[
            # Optional: Impute missing categorical values if necessary
            # ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(
                categories=[known_categories.get(f, []) for f in categorical_features],
                handle_unknown='ignore', # Still crucial for data drift / minor inconsistencies
                sparse_output=True))
        ])
        transformers.append(('cat', categorical_pipeline, categorical_features))
        logging.info(f"Preprocessor: Applying OneHotEncoder (sparse) to: {categorical_features}")
    else:
        logging.info("Preprocessor: No categorical features specified.") # Changed from warning

    if not transformers:
        raise ValueError("No numerical or categorical features specified or found for preprocessing.")

    preprocessor = ColumnTransformer(transformers=transformers, remainder='drop', n_jobs=1)
    return preprocessor

# --- Data Cleaning Function (Reusable) ---
def clean_data_chunk(df, numerical_cols, categorical_cols, chunk_num="N/A"):
    """Applies cleaning steps (numeric conversion, infinity handling) to a DataFrame."""
    df.columns = df.columns.str.strip() # Strip whitespace first

    # Clean numerical features
    for col in numerical_cols:
        if col in df.columns:
            original_dtype = df[col].dtype
            # Convert to numeric, coercing errors (strings) to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if df[col].isnull().any() and not pd.api.types.is_numeric_dtype(original_dtype):
                logging.debug(f"Chunk {chunk_num}, Col '{col}': Coerced non-numeric to NaN.")

            # Handle infinities AFTER converting strings
            if df[col].dtype.kind in 'if': # Check float/int
                inf_mask = np.isinf(df[col])
                if inf_mask.any():
                    num_inf = inf_mask.sum()
                    logging.warning(f"Chunk {chunk_num}, Col '{col}': Replaced {num_inf} infinities with NaN.")
                    df[col] = df[col].replace([np.inf, -np.inf], np.nan)
        # else: logging.warning(f"Expected numerical column '{col}' not found during cleaning.") # Optional verbosity

    # Add specific cleaning for categorical if needed here

    return df

# --- Function to Load/Sample/Clean/Transform Data using EXISTING Preprocessor ---
def load_and_process_data(data_path, preprocessor, features_dict, chunk_size, target_sample_size=None, is_rf_data=False):
    """Loads data (chunked if sampling), cleans, and transforms using a loaded preprocessor."""
    logging.info(f"Loading/Processing data from: {data_path}")
    if not os.path.isfile(data_path):
        logging.error(f"Data file not found: {data_path}")
        return None, None # Return None for X and y

    # Use features known by the loaded preprocessor
    numerical_cols = features_dict.get('num', [])
    categorical_cols = features_dict.get('cat', [])
    all_feature_cols = features_dict.get('all', [])
    if not all_feature_cols: # Check if feature list is valid
         logging.error("Feature dictionary provided to load_and_process_data is empty or invalid.")
         return None, None
         
    label_col_present = False
    y_data = None

    # Decide whether to chunk/sample or load all
    load_all = target_sample_size is None

    processed_data_list = []
    y_list = [] # Store labels if present and needed

    if load_all:
        logging.info("Loading entire file (assuming it fits memory)...")
        try:
            df_full = pd.read_csv(data_path, low_memory=False)
            df_full = clean_data_chunk(df_full, numerical_cols, categorical_cols, chunk_num="FullLoad")
            df_full = optimize_dtypes(df_full)

            missing_cols = [f for f in all_feature_cols if f not in df_full.columns]
            if missing_cols:
                logging.error(f"Data file {data_path} is missing required columns defined by preprocessor: {missing_cols}")
                return None, None # Cannot transform if columns used by preprocessor are missing

            label_col_present = LABEL_COLUMN in df_full.columns
            if is_rf_data and label_col_present:
                 y_data = df_full[LABEL_COLUMN].copy()

            X_features = df_full[all_feature_cols] # Select only features known to preprocessor
            X_processed = preprocessor.transform(X_features)
            processed_data_list.append(X_processed) # List with one item
            logging.info(f"Successfully loaded and transformed entire file. Shape: {X_processed.shape}")
            del df_full, X_features; gc.collect()

        except MemoryError:
             logging.error(f"MemoryError loading entire file: {data_path}. File may be too large.")
             return None, None
        except ValueError as ve: # Catch transform errors (e.g., unexpected values)
             logging.error(f"ValueError during transform of {data_path}: {ve}. Check data cleaning and preprocessor compatibility.")
             return None, None
        except Exception as e:
             logging.error(f"Error loading/processing file {data_path}: {e}", exc_info=True)
             return None, None
    else: # Chunk and Sample
        logging.info(f"Loading via chunks/sampling (target: {target_sample_size:,})...")
        sampled_chunks = []
        total_rows_processed = 0
        estimated_total_rows = 1
        first_chunk = True

        try:
            reader = pd.read_csv(data_path, chunksize=chunk_size, iterator=True, low_memory=False)
            for i, chunk in enumerate(reader):
                chunk = clean_data_chunk(chunk, numerical_cols, categorical_cols, chunk_num=f"Load:{i+1}")
                chunk = optimize_dtypes(chunk)

                # Select required columns (features + label if needed) defined by preprocessor
                required_cols = all_feature_cols + ([LABEL_COLUMN] if is_rf_data else [])
                cols_in_chunk = [c for c in required_cols if c in chunk.columns]
                missing_req_cols = [c for c in all_feature_cols if c not in chunk.columns] # Check features needed by preprocessor specifically
                if missing_req_cols:
                     logging.error(f"Chunk {i+1} is missing required columns for transform: {missing_req_cols}. Stopping processing for this file.")
                     try: reader.close()
                     except: pass
                     return None, None # Cannot proceed if features are missing

                if first_chunk:
                    # Check for label only once if needed
                    label_col_present = LABEL_COLUMN in chunk.columns
                    if is_rf_data and not label_col_present:
                        logging.warning(f"Label column '{LABEL_COLUMN}' not found in first chunk of {data_path} (required for RF).")
                        # Continue sampling features, but y_data will remain None

                    # Estimate size (only for sampling calculation)
                    try:
                        file_size = os.path.getsize(data_path)
                        bytes_per_row_est = chunk.memory_usage(index=True,deep=True).sum()/max(1,len(chunk))
                        if bytes_per_row_est > 0: estimated_total_rows = file_size/bytes_per_row_est
                    except Exception: pass # Ignore estimation errors here
                    first_chunk = False
                
                chunk = chunk[[c for c in cols_in_chunk if c in chunk.columns]] # Select available needed columns

                # Sampling Logic
                rows_in_chunk = len(chunk)
                sample_n_this_chunk = 0
                if estimated_total_rows > 0 and rows_in_chunk > 0:
                    sample_frac_this_chunk = target_sample_size / estimated_total_rows
                    sample_n_this_chunk = min(rows_in_chunk, int(np.ceil(rows_in_chunk*sample_frac_this_chunk)))
                if sample_n_this_chunk < 1 and target_sample_size > 0 and rows_in_chunk > 0: sample_n_this_chunk = 1

                current_sample_total = sum(len(sc) for sc in sampled_chunks)
                remaining_needed = max(0, target_sample_size - current_sample_total)
                sample_n_this_chunk = min(sample_n_this_chunk, remaining_needed)

                if sample_n_this_chunk > 0 and not chunk.empty:
                    sampled_chunks.append(chunk.sample(n=sample_n_this_chunk, random_state=42))

                total_rows_processed += rows_in_chunk
                logging.info(f"  Load Chunk {i+1}: Processed {total_rows_processed:,}. Sample size: {current_sample_total + (len(sampled_chunks[-1]) if sample_n_this_chunk > 0 and sampled_chunks else 0):,}")
                del chunk; gc.collect()
            try: reader.close()
            except: pass
            logging.info("Finished reading/sampling chunks.")

            if not sampled_chunks:
                 logging.error("No data sampled from file.")
                 return None, None

            # Assemble, process, and store labels
            logging.info("Assembling and transforming sampled data...")
            sampled_data = pd.concat(sampled_chunks, ignore_index=True); del sampled_chunks; gc.collect()

            missing_cols_final = [f for f in all_feature_cols if f not in sampled_data.columns]
            if missing_cols_final:
                 logging.error(f"Assembled sampled data is missing required columns: {missing_cols_final}")
                 return None, None

            if is_rf_data and label_col_present: # Check again on assembled data
                 if LABEL_COLUMN in sampled_data.columns:
                     y_data = sampled_data[LABEL_COLUMN].copy()
                 else:
                     logging.error(f"Label column '{LABEL_COLUMN}' missing in assembled sample. Cannot provide labels for RF.")
                     # Proceed with features, y_data remains None

            X_features = sampled_data[all_feature_cols]
            try:
                X_processed = preprocessor.transform(X_features)
                processed_data_list.append(X_processed)
                logging.info(f"Successfully transformed sampled data. Shape: {X_processed.shape}")
            except ValueError as ve:
                 logging.error(f"ValueError transforming sampled data from {data_path}: {ve}. Check cleaning/preprocessor.")
                 return None, y_data # Return None for X, maybe y if collected
            except Exception as e:
                logging.error(f"Error transforming sampled data from {data_path}: {e}", exc_info=True)
                return None, y_data # Return None for X, maybe y if collected
            finally:
                 del sampled_data, X_features; gc.collect()

        except FileNotFoundError:
            logging.error(f"Data file not found during chunk processing: {data_path}")
            return None, None
        except pd.errors.EmptyDataError:
             logging.error(f"Data file is empty: {data_path}")
             return None, None
        except Exception as e:
             logging.error(f"Error during chunked loading/processing of {data_path}: {e}", exc_info=True)
             return None, None

    # Combine processed data (typically just one item unless transform adapted)
    if not processed_data_list:
        return None, y_data # Return potentially collected y_data even if X failed

    # Assuming sparse matrix output from ColumnTransformer, use vstack
    if hasattr(processed_data_list[0], 'format'): # Check if it looks like a sparse matrix
         from scipy.sparse import vstack
         try:
             final_X_processed = vstack(processed_data_list, format='csr')
         except Exception as e:
             logging.error(f"Failed to vstack processed sparse data: {e}. Trying concat (might be dense).")
             # Fallback for potentially dense output or other types
             try: final_X_processed = pd.concat(processed_data_list) if len(processed_data_list) > 1 else processed_data_list[0]
             except: logging.error("Failed to combine processed data parts."); return None, y_data
    else: # Assume pandas DataFrame or compatible
        try: final_X_processed = pd.concat(processed_data_list) if len(processed_data_list) > 1 else processed_data_list[0]
        except Exception as e:
            logging.error(f"Failed to concat processed data parts: {e}")
            return None, y_data

    return final_X_processed, y_data


# --- Main Training Function ---
def train_models_selective(
    rf_data_path,
    if_data_path,
    train_rf_model,
    train_if_model,
    target_sample_size, # Sample size from RF data if fitting preprocessor
    chunk_size,         # Chunk size for RF data path if fitting preprocessor
    n_estimators,
    max_depth,
    n_jobs):
    """Loads data, preprocesses, and selectively trains RF and/or IF models."""

    logging.info("Starting selective training process...")
    logging.info(f"Train RF: {train_rf_model}, RF Data: {rf_data_path}")
    logging.info(f"Train IF: {train_if_model}, IF Data: {if_data_path}")
    os.makedirs(MODELS_DIR, exist_ok=True)

    # --- Pre-checks based on flags (as before) ---
    if not train_rf_model and not train_if_model: logging.warning("Nothing to do."); return
    if train_rf_model and not rf_data_path: logging.error("RF training requested but no --rf-data path."); return
    if train_if_model and not if_data_path: logging.error("IF training requested but no --if-data path."); return
    # Need rf_data path for preprocessor even if only training IF, UNLESS preprocessor exists
    preprocessor_exists = os.path.exists(PREPROCESSOR_OBJECT_PATH)
    if not preprocessor_exists and not rf_data_path:
        logging.error("Preprocessor needs fitting (file not found), but no --rf-data path provided."); return


    # --- Variables Initialization ---
    preprocessor = None
    actual_features = None # Features loaded from file or identified
    X_processed_rf_sample = None
    y_rf_sample = None
    X_processed_if_base = None

    # --- Phase 1: Load or Fit Preprocessor ---
    if preprocessor_exists:
        logging.info(f"Attempting to load existing preprocessor object: {PREPROCESSOR_OBJECT_PATH}")
        try:
            loaded_object = joblib.load(PREPROCESSOR_OBJECT_PATH)
            if isinstance(loaded_object, dict) and 'preprocessor' in loaded_object and 'features' in loaded_object:
                preprocessor = loaded_object['preprocessor']
                actual_features = loaded_object['features'] # Load features used by this preprocessor
                logging.info("Successfully loaded preprocessor and associated features.")
                if not actual_features or not actual_features.get('all'): # More robust check
                     logging.warning("Loaded features dictionary seems empty or invalid. Retrying fitting.")
                     preprocessor = None # Force refitting
                else:
                     logging.info(f"Loaded features - Num: {len(actual_features.get('num',[]))}, Cat: {len(actual_features.get('cat',[]))}, All: {len(actual_features.get('all',[]))}")
            else:
                logging.warning("Existing preprocessor file has unexpected format. Will attempt to refit.")
                preprocessor = None
        except Exception as e:
            logging.error(f"Error loading existing preprocessor object: {e}. Will attempt to refit.", exc_info=True)
            preprocessor = None
    else:
        logging.info("No existing preprocessor found. Fitting from scratch...")
        # preprocessor is already None

    if preprocessor is None: # Need to fit it
        logging.info(f"Fitting preprocessor using RF data file: {rf_data_path}")
        if not rf_data_path or not os.path.isfile(rf_data_path): # Check again
             logging.error(f"RF data file for fitting not found or not specified: {rf_data_path}")
             return

        # --- Original Chunking/Sampling/Fitting Logic ---
        sampled_chunks_fit = []
        all_categories_fit = defaultdict(set)
        total_rows_processed_fit = 0
        estimated_total_rows_fit = 1
        actual_features = {} # Reset features dict for fresh identification

        try:
            reader_fit = pd.read_csv(rf_data_path, chunksize=chunk_size, iterator=True, low_memory=False)
            for i, chunk in enumerate(reader_fit):
                logging.debug(f"Fitting phase: Processing chunk {i+1}") # Debug level for fitting chunks
                if i == 0: # Identify features
                    chunk.columns = chunk.columns.str.strip()
                    actual_features['num'] = [f for f in DEFAULT_NUMERICAL_FEATURES if f in chunk.columns]
                    actual_features['cat'] = [f for f in DEFAULT_CATEGORICAL_FEATURES if f in chunk.columns]
                    actual_features['all'] = actual_features['num'] + actual_features['cat']
                    if not actual_features['all']:
                        logging.error("No relevant features found in first chunk for fitting.")
                        try: reader_fit.close()
                        except: pass
                        return
                    logging.info(f"Fitting: Identified Numerical Features: {actual_features['num']}")
                    logging.info(f"Fitting: Identified Categorical Features: {actual_features['cat']}")
                    # Estimate size
                    try:
                        file_size = os.path.getsize(rf_data_path)
                        bytes_per_row_est = chunk.memory_usage(index=True,deep=True).sum()/max(1,len(chunk))
                        if bytes_per_row_est > 0: estimated_total_rows_fit = file_size/bytes_per_row_est
                    except Exception: pass # Ignore estimation errors

                chunk = clean_data_chunk(chunk, actual_features['num'], actual_features['cat'], chunk_num=f"Fit:{i+1}")
                chunk = optimize_dtypes(chunk)
                cols_to_keep_fit = actual_features['all'] + ([LABEL_COLUMN] if LABEL_COLUMN in chunk.columns else [])
                cols_to_keep_fit = [c for c in cols_to_keep_fit if c in chunk.columns]
                chunk = chunk[cols_to_keep_fit]

                # Gather categories
                for col in actual_features['cat']:
                     if col in chunk.columns: all_categories_fit[col].update(chunk[col].dropna().unique())

                # Sampling Logic
                rows_in_chunk = len(chunk)
                sample_n_this_chunk = 0
                if estimated_total_rows_fit > 0 and rows_in_chunk > 0:
                    sample_frac_this_chunk = target_sample_size / estimated_total_rows_fit
                    sample_n_this_chunk = min(rows_in_chunk, int(np.ceil(rows_in_chunk*sample_frac_this_chunk)))
                if sample_n_this_chunk < 1 and target_sample_size > 0 and rows_in_chunk > 0: sample_n_this_chunk = 1
                current_sample_total = sum(len(sc) for sc in sampled_chunks_fit)
                remaining_needed = max(0, target_sample_size - current_sample_total)
                sample_n_this_chunk = min(sample_n_this_chunk, remaining_needed)

                if sample_n_this_chunk > 0 and not chunk.empty:
                    sampled_chunks_fit.append(chunk.sample(n=sample_n_this_chunk, random_state=42))

                total_rows_processed_fit += rows_in_chunk
                if (i+1) % 10 == 0: # Log progress occasionally
                    logging.info(f"  Fitting phase chunk {i+1}: Processed {total_rows_processed_fit:,}. Sample size: {current_sample_total + (len(sampled_chunks_fit[-1]) if sample_n_this_chunk > 0 and sampled_chunks_fit else 0):,}")

                del chunk; gc.collect()
            try: reader_fit.close()
            except: pass
            logging.info("Finished reading RF data chunks for fitting.")

            if not sampled_chunks_fit: logging.error("No data sampled for fitting."); return

            sampled_data_fit = pd.concat(sampled_chunks_fit, ignore_index=True); del sampled_chunks_fit; gc.collect()
            logging.info(f"Assembled sample data shape for fitting: {sampled_data_fit.shape}")

            known_categories_list = {k: sorted(list(v)) for k, v in all_categories_fit.items()}
            del all_categories_fit; gc.collect()

            # Check if sample is empty before selecting features
            if sampled_data_fit.empty:
                 logging.error("Sampled data for fitting is empty after assembly.")
                 return

            X_sample_fit = sampled_data_fit[actual_features['all']] # Use features identified in this run
            del sampled_data_fit; gc.collect() # Free memory early

            # Check if feature DataFrame is empty
            if X_sample_fit.empty:
                 logging.error("Feature sample (X_sample_fit) is empty before fitting preprocessor.")
                 return

            preprocessor = build_preprocessor(actual_features['num'], actual_features['cat'], known_categories_list)
            logging.info("Fitting preprocessor on the new sample...")
            preprocessor.fit(X_sample_fit)

            # --- Save the NEW preprocessor AND features ---
            preprocessor_object_to_save = {
                'preprocessor': preprocessor,
                'features': actual_features # Save the features identified during this fit
            }
            joblib.dump(preprocessor_object_to_save, PREPROCESSOR_OBJECT_PATH)
            logging.info(f"Preprocessor fitted and saved (with features) to {PREPROCESSOR_OBJECT_PATH}")

            del X_sample_fit; gc.collect() # Clean up fitting data

        except FileNotFoundError:
            logging.error(f"RF data file not found during fitting: {rf_data_path}")
            return
        except pd.errors.EmptyDataError:
            logging.error(f"RF data file is empty during fitting: {rf_data_path}")
            return
        except Exception as e:
             logging.error(f"Error during preprocessor fitting phase: {e}", exc_info=True)
             return # Cannot proceed without preprocessor

    # --- Phase 2: Load/Process Data for Training (using the ready preprocessor) ---
    if preprocessor is None or actual_features is None or not actual_features.get('all'):
         logging.error("Preprocessor or its associated features are not available. Cannot proceed.")
         return

    # --- Load/Process RF Data (if needed for training) ---
    if train_rf_model:
        logging.info("Loading/Processing RF data for training...")
        X_processed_rf_sample, y_rf_sample = load_and_process_data(
            data_path=rf_data_path,
            preprocessor=preprocessor,
            features_dict=actual_features, # Use features associated with the preprocessor
            chunk_size=chunk_size,
            target_sample_size=target_sample_size, # Sample the RF data for training
            is_rf_data=True # To handle label column
        )
        if X_processed_rf_sample is None or y_rf_sample is None:
             logging.error("Failed to load/process RF data for training. Skipping RF model.")
             train_rf_model = False # Disable RF training if data failed
        elif y_rf_sample.isnull().all(): # Check if label column was entirely NaN
             logging.error("Label column in processed RF data is all null. Skipping RF model.")
             train_rf_model = False


    # --- Load/Process IF Data (if needed for training) ---
    if train_if_model:
        logging.info("Loading/Processing IF data for training...")
        # Load ALL IF data (target_sample_size=None), no label needed
        X_processed_if_base, _ = load_and_process_data(
            data_path=if_data_path,
            preprocessor=preprocessor,
            features_dict=actual_features, # Use features associated with the preprocessor
            chunk_size=chunk_size, # Chunk size still relevant for memory if file is large
            target_sample_size=None, # Load all
            is_rf_data=False
        )
        if X_processed_if_base is None:
            logging.error("Failed to load/process IF data for training. Skipping IF model.")
            train_if_model = False # Disable IF training if data failed

    # --- Phase 3: Train Models Selectively ---
    logging.info(f"Starting model training phase (RF: {train_rf_model}, IF: {train_if_model})...")

    # --- Train RF ---
    if train_rf_model: # Re-check flag in case data loading failed
        logging.info("Proceeding with Random Forest training...")
        try:
             unique_labels = y_rf_sample.unique()
             # Check for NaNs in unique labels as well
             if pd.isna(unique_labels).any():
                 logging.warning(f"NaN found in unique labels: {unique_labels}. Check label column processing.")
                 # Optionally remove NaNs before checking length, or handle as separate category
                 unique_labels = unique_labels[~pd.isna(unique_labels)]

             if len(unique_labels) < 2:
                 logging.warning(f"Loaded RF sample has < 2 non-NaN unique labels ({unique_labels}). Skipping RF.")
             else:
                 logging.info(f"Training RF with {X_processed_rf_sample.shape[0]} samples.")
                 X_train, X_test, y_train, y_test = train_test_split(
                     X_processed_rf_sample, y_rf_sample, test_size=0.2, random_state=42,
                     stratify=y_rf_sample if len(unique_labels) > 1 else None)

                 rf_classifier = RandomForestClassifier(
                     n_estimators=n_estimators, max_depth=max_depth, random_state=42,
                     class_weight='balanced', n_jobs=n_jobs, min_samples_leaf=5)
                 rf_classifier.fit(X_train, y_train)
                 logging.info("RF Training completed.")

                 # Evaluation
                 try:
                     logging.info("Evaluating RF model...")
                     accuracy = rf_classifier.score(X_test, y_test)
                     logging.info(f"RF Test Sample Accuracy: {accuracy:.4f}")
                 except Exception as eval_e:
                      logging.warning(f"Could not complete RF evaluation: {eval_e}")

                 # Save RF Model
                 joblib.dump(rf_classifier, RF_MODEL_PATH)
                 logging.info(f"Random Forest model saved to {RF_MODEL_PATH}")

                 del rf_classifier, X_train, X_test, y_train, y_test; gc.collect()
        except Exception as e:
             logging.error(f"Error during RF training execution: {e}", exc_info=True)
    elif args.train_rf: # Log if RF was requested but prerequisites failed
         logging.warning("Skipping RF training because required data was not loaded/processed correctly.")


    # --- Train IF ---
    if train_if_model: # Re-check flag
        logging.info("Proceeding with Isolation Forest training...")
        try:
             if X_processed_if_base is None or X_processed_if_base.shape[0] < 2:
                  logging.warning(f"Not enough valid data for IF training (Shape: {X_processed_if_base.shape if X_processed_if_base is not None else 'None'}). Skipping.")
             else:
                  logging.info(f"Training Isolation Forest on data shape {X_processed_if_base.shape}...")
                  if_model = IsolationForest(
                      n_estimators=n_estimators, contamination='auto', random_state=42, n_jobs=n_jobs, max_features=0.8)
                  if_model.fit(X_processed_if_base)
                  logging.info("IF Training complete.")
                  joblib.dump(if_model, IF_MODEL_PATH)
                  logging.info(f"Isolation Forest model saved to {IF_MODEL_PATH}")
                  del if_model; gc.collect()
        except Exception as e:
             logging.error(f"Error during Isolation Forest training execution: {e}", exc_info=True)
    elif args.train_if: # Log if IF was requested but prerequisites failed
         logging.warning("Skipping IF training because required data was not loaded/processed correctly.")


    # --- Final Cleanup ---
    if 'X_processed_rf_sample' in locals() and X_processed_rf_sample is not None: del X_processed_rf_sample
    if 'y_rf_sample' in locals() and y_rf_sample is not None: del y_rf_sample
    if 'X_processed_if_base' in locals() and X_processed_if_base is not None: del X_processed_if_base
    gc.collect()
    logging.info("Selective training process finished.")


# --- Main execution block with Argument Validation ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Selectively train RF/IF models, loading existing preprocessor if available.")

    # Data Sources
    parser.add_argument("--rf-data", required=False, # Required only if fitting preprocessor or training RF
                        help="Path to CSV for RF training AND Preprocessor fitting (if preprocessor file doesn't exist).")
    parser.add_argument("--if-data", required=False, # Required only if training IF
                        help="Path to CSV for Isolation Forest training.")

    # Model Selection Flags
    parser.add_argument("--train-rf", action='store_true', default=False,
                        help=f"If set, train Random Forest using --rf-data.")
    parser.add_argument("--train-if", action='store_true', default=False,
                        help=f"If set, train Isolation Forest using --if-data.")

    # Training Parameters
    parser.add_argument("--target-sample-size", type=int, default=DEFAULT_TARGET_SAMPLE_SIZE,
                        help=f"Target rows to sample from RF data if fitting preprocessor/training RF. Default: {DEFAULT_TARGET_SAMPLE_SIZE:,}")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE,
                        help=f"Rows per chunk if reading RF data for fitting. Default: {DEFAULT_CHUNK_SIZE:,}")
    parser.add_argument("--n-estimators", type=int, default=DEFAULT_N_ESTIMATORS,
                        help=f"Number of trees in the forests. Default: {DEFAULT_N_ESTIMATORS}")
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH,
                        help=f"Maximum depth of trees (for RF). Default: {DEFAULT_MAX_DEPTH}")
    parser.add_argument("--n-jobs", type=int, default=DEFAULT_N_JOBS,
                        help=f"Number of CPU cores (-1 for all, 1 uses less peak memory). Default: {DEFAULT_N_JOBS}")

    args = parser.parse_args()

    # --- Input Argument Validation ---
    valid = True
    if not args.train_rf and not args.train_if:
        parser.error("Must specify --train-rf and/or --train-if.")
        valid = False

    # Check RF path requirements
    preprocessor_exists = os.path.exists(PREPROCESSOR_OBJECT_PATH)
    if args.train_rf:
        if not args.rf_data: parser.error("--train-rf requires --rf-data."); valid = False
        elif not os.path.isfile(args.rf_data): parser.error(f"RF data file not found: {args.rf_data}"); valid = False

    # Check IF path requirements
    if args.train_if:
        if not args.if_data: parser.error("--train-if requires --if-data."); valid = False
        elif not os.path.isfile(args.if_data): parser.error(f"IF data file not found: {args.if_data}"); valid = False

    # Check if RF path is needed for potential preprocessor fitting
    if not preprocessor_exists: # Only need rf_data for fitting if preprocessor doesn't exist
        if not args.rf_data:
             parser.error(f"Preprocessor file ({PREPROCESSOR_OBJECT_PATH}) not found. Must specify --rf-data for initial fitting.")
             valid = False
        elif not os.path.isfile(args.rf_data):
             # Need to check rf_data existence again here specifically for fitting
             parser.error(f"Preprocessor needs fitting, but RF data file not found: {args.rf_data}")
             valid = False

    # Check numerical arguments are positive
    if args.target_sample_size <= 0:
        parser.error(f"target_sample_size must be positive. Got: {args.target_sample_size}")
        valid = False
    if args.chunk_size <= 0:
        parser.error(f"chunk_size must be positive. Got: {args.chunk_size}")
        valid = False
    if args.n_estimators <= 0:
        parser.error(f"n_estimators must be positive. Got: {args.n_estimators}")
        valid = False
    if args.max_depth <= 0:
        parser.error(f"max_depth must be positive. Got: {args.max_depth}")
        valid = False

    # Check n_jobs
    if not (args.n_jobs >= 1 or args.n_jobs == -1):
        parser.error(f"n_jobs must be a positive integer or -1. Got: {args.n_jobs}")
        valid = False

    # --- Proceed only if all validations passed ---
    if valid:
        train_models_selective(
            rf_data_path=args.rf_data,
            if_data_path=args.if_data,
            train_rf_model=args.train_rf,
            train_if_model=args.train_if,
            target_sample_size=args.target_sample_size,
            chunk_size=args.chunk_size,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            n_jobs=args.n_jobs
        )
    else:
        # parser.error already exits
        pass