import pandas as pd
import joblib
import os
import argparse
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
MODELS_DIR = "models"
# **IMPORTANT: Update path name to match train.py**
PREPROCESSOR_OBJECT_PATH = os.path.join(MODELS_DIR, "preprocessor_and_features.joblib")
RF_MODEL_PATH = os.path.join(MODELS_DIR, "rf_model.joblib")
IF_MODEL_PATH = os.path.join(MODELS_DIR, "if_model.joblib")
OUTPUT_DIR = "analyse/processed_output/"

# --- Helper: Data Cleaning (Should match train.py's logic) ---
# It's good practice to apply the same cleaning before transformation
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
                    # Log as info/warning in processing, might be expected or error
                    logging.info(f"Chunk {chunk_num}, Col '{col}': Replacing {num_inf} infinities with NaN.")
                    df[col] = df[col].replace([np.inf, -np.inf], np.nan)
    return df

# --- Prediction Function ---
def process_predict_and_save(data_path, output_filename):
    """Loads models, processes new data, predicts, and saves results."""
    logging.info(f"Starting processing for: {data_path}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # --- Load Preprocessor Object (Dict containing preprocessor + features) ---
    preprocessor = None
    actual_features = None
    try:
        loaded_object = joblib.load(PREPROCESSOR_OBJECT_PATH)
        if isinstance(loaded_object, dict) and 'preprocessor' in loaded_object and 'features' in loaded_object:
            preprocessor = loaded_object['preprocessor']
            actual_features = loaded_object['features']
            logging.info("Preprocessor object (including features) loaded successfully.")
            if not actual_features or not actual_features.get('all'):
                 raise ValueError("Loaded features dictionary is empty or invalid.")
            logging.info(f"Using features defined by loaded preprocessor: {actual_features.get('all')}")
        else:
             raise ValueError("Loaded preprocessor file has an unexpected format.")

    except FileNotFoundError:
        logging.error(f"Preprocessor object file not found at {PREPROCESSOR_OBJECT_PATH}. Run train.py first.")
        return
    except Exception as e:
        logging.error(f"Error loading preprocessor object: {e}", exc_info=True)
        return

    # --- Load Models (RF & IF) ---
    rf_model = None
    if os.path.exists(RF_MODEL_PATH):
        try:
            rf_model = joblib.load(RF_MODEL_PATH)
            logging.info("Random Forest model loaded.")
        except Exception as e:
            logging.warning(f"Could not load RF model from {RF_MODEL_PATH}: {e}")
    else:
        logging.info("RF model file not found. Skipping RF predictions.")

    if_model = None
    if os.path.exists(IF_MODEL_PATH):
        try:
            if_model = joblib.load(IF_MODEL_PATH)
            logging.info("Isolation Forest model loaded.")
        except Exception as e:
            logging.warning(f"Could not load IF model from {IF_MODEL_PATH}: {e}")
            # Continue without IF if it fails to load? Or return? Decide based on requirements.
            # return
    else:
        logging.info("IF model file not found. Skipping IF predictions.")

    # --- Load New Data ---
    try:
        # Load the whole file - adjust if new data can also be huge
        df_new = pd.read_csv(data_path, low_memory=False)
        logging.info(f"Loaded new data with shape: {df_new.shape}")
        # Keep original data to append predictions to
        df_output = df_new.copy()
    except FileNotFoundError:
        logging.error(f"New data file not found: {data_path}")
        return
    except pd.errors.EmptyDataError:
         logging.error(f"New data file is empty: {data_path}")
         return
    except Exception as e:
        logging.error(f"Error loading new data: {e}", exc_info=True)
        return

    # --- Clean and Prepare Features ---
    # Use the feature names loaded alongside the preprocessor
    numerical_cols = actual_features.get('num', [])
    categorical_cols = actual_features.get('cat', [])
    all_feature_cols = actual_features.get('all', [])

    if not all_feature_cols:
         logging.error("No feature names found in loaded preprocessor object.")
         return

    # Clean the new data using the same logic as training chunks
    df_new = clean_data_chunk(df_new, numerical_cols, categorical_cols, chunk_num="NewData")

    # Ensure required feature columns exist in the new data
    missing_cols = [f for f in all_feature_cols if f not in df_new.columns]
    if missing_cols:
        logging.error(f"New data file ({data_path}) is missing required feature columns defined by preprocessor: {missing_cols}")
        logging.warning("Attempting to proceed without missing columns, but results may be inaccurate or fail.")
        # Select only the available features among the required ones
        available_feature_cols = [f for f in all_feature_cols if f in df_new.columns]
        if not available_feature_cols:
             logging.error("No usable feature columns remaining after checking for missing ones. Cannot proceed.")
             return
        X_new = df_new[available_feature_cols]
        # Note: Transformation might still fail if the preprocessor pipeline expects all columns.
    else:
        # Select only the features the preprocessor expects
        X_new = df_new[all_feature_cols]


    # --- Preprocess New Data ---
    try:
        # **CRITICAL FIX:** Use the extracted preprocessor object
        X_new_processed = preprocessor.transform(X_new)
        logging.info("New data preprocessed successfully.")
        logging.info(f"Processed data shape: {X_new_processed.shape}")
    except ValueError as ve:
         # More specific error for transform issues (often shape or unseen values if handle_unknown='error')
         logging.error(f"ValueError during preprocessing new data: {ve}")
         logging.error("This might be due to unexpected values (if not handled by cleaning/imputer/OHE) or column mismatch.")
         return
    except Exception as e:
        logging.error(f"Error preprocessing new data: {e}", exc_info=True)
        return

    # --- Make Predictions ---

    # RF Prediction (if model loaded)
    if rf_model:
        try:
            rf_predictions = rf_model.predict(X_new_processed)
            df_output['rf_prediction'] = rf_predictions
            logging.info("RF predictions generated.")
            # Optionally add probabilities if needed
            try:
                 rf_probabilities = rf_model.predict_proba(X_new_processed)
                 # Get the probability of the predicted class
                 df_output['rf_confidence'] = np.max(rf_probabilities, axis=1)
                 logging.info("RF confidence scores generated.")
            except AttributeError:
                 logging.warning("RF model doesn't support predict_proba or failed.")
                 df_output['rf_confidence'] = np.nan
            except Exception as proba_e:
                 logging.warning(f"Error getting RF probabilities: {proba_e}")
                 df_output['rf_confidence'] = np.nan

        except Exception as e:
            logging.warning(f"Error during RF prediction: {e}")
            df_output['rf_prediction'] = 'Error'
            df_output['rf_confidence'] = 0.0

    # IF Prediction (if model loaded)
    if if_model:
        try:
            if_scores = if_model.score_samples(X_new_processed) # Lower score = more anomalous
            if_preds = if_model.predict(X_new_processed)       # -1 = anomaly, 1 = inlier

            df_output['if_anomaly_score'] = if_scores
            df_output['if_is_anomaly'] = (if_preds == -1)
            logging.info("IF anomaly scores and predictions generated.")
        except Exception as e:
            logging.warning(f"Error during IF prediction: {e}")
            df_output['if_anomaly_score'] = 0.0 # Or np.nan
            df_output['if_is_anomaly'] = False # Default to not anomaly on error

    # --- Save Results ---
    try:
        df_output.to_csv(output_path, index=False)
        logging.info(f"Processed data with predictions saved to: {output_path}")
    except Exception as e:
        logging.error(f"Error saving processed data to {output_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process new network flow data using trained models.")
    parser.add_argument("data_path", help="Path to the new data CSV file.")
    parser.add_argument("output_filename", help="Filename for the output CSV in the 'processed_output' directory.")

    # Add validation for input arguments if desired
    args = parser.parse_args()

    if not os.path.isfile(args.data_path):
        print(f"Error: Input data file not found: {args.data_path}")
        exit(1)

    process_predict_and_save(args.data_path, args.output_filename)