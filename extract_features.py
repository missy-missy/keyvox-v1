import os
import librosa
import numpy as np
import json

# --- Configuration ---
# This should match the sample rate of your recordings
# Your script uses 44100, but 16000 or 22050 are common for speech processing.
# Librosa will resample it for you, but it's good practice to be aware.
TARGET_SAMPLE_RATE = 22050 

# --- Get the absolute path of the directory where this script is located ---
# THIS LINE MUST COME FIRST
script_dir = os.path.dirname(os.path.abspath(__file__))

# Directory where your recording script saves the .wav files
SOURCE_FOLDER = os.path.join(script_dir, "recordings")

# File where we will save the processed data
JSON_PATH = os.path.join(script_dir, "data_features.json")


# MFCC extraction parameters
# These are standard values, but you can tune them
N_MFCC = 13       # Number of MFCCs to extract
N_FFT = 2048      # Window size for the Fast Fourier Transform
HOP_LENGTH = 512  # Number of samples between successive frames

def preprocess_and_extract_features(folder_path):
    """
    Loads audio files, preprocesses them, extracts MFCCs, and returns the data.
    
    :param folder_path (str): Path to the folder containing .wav files.
    :return data (dict): A dictionary containing mappings, labels, and MFCCs.
    """
    
    data = {
        "mappings": [],
        "labels": [],
        "mfccs": []
    }
    
    if not os.path.exists(folder_path):
        print(f"❌ Error: The folder '{folder_path}' does not exist. Please run the recording script first.")
        return None

    print("Starting feature extraction...")
    for i, filename in enumerate(os.listdir(folder_path)):
        if filename.endswith(".wav"):
            file_path = os.path.join(folder_path, filename)
            print(f"Processing: {file_path}")

            try:
                signal, sr = librosa.load(file_path, sr=TARGET_SAMPLE_RATE, mono=True)
                
                # Use a higher top_db for more aggressive silence trimming
                signal, _ = librosa.effects.trim(signal, top_db=25)

                if len(signal) == 0:
                    print(f"  ⚠️ File {filename} is all silence. Skipping.")
                    continue

                mfccs = librosa.feature.mfcc(y=signal, 
                                             sr=sr, 
                                             n_mfcc=N_MFCC, 
                                             n_fft=N_FFT, 
                                             hop_length=HOP_LENGTH)
                
                mfccs = mfccs.T
                
                if mfccs.shape[0] > 0: # Check if there are any frames
                    # THIS IS THE CRITICAL FIX: Convert the numpy array to a nested list.
                    data["mfccs"].append(mfccs.tolist()) 
                    data["mappings"].append(filename)
                    data["labels"].append(i) # For now, each file is its own class
                    print(f"  ✅ Successfully extracted MFCCs with shape: {mfccs.shape}")
                else:
                    print(f"  ⚠️ Could not extract MFCCs from {filename}. File might be too short after trimming.")

            except Exception as e:
                print(f"  ❌ Error processing {filename}: {e}")

    return data
def save_data_to_json(data, json_path):
    """
    Saves the extracted features and labels to a JSON file.
    
    :param data (dict): The data dictionary to save.
    :param json_path (str): The path to the output JSON file.
    """
    if data is None or not data["mfccs"]:
        print("No data was extracted. JSON file will not be created.")
        return

    print(f"\nSaving data to {json_path}...")
    with open(json_path, "w") as fp:
        json.dump(data, fp, indent=4)
    print("✅ Data successfully saved.")


if __name__ == "__main__":
    # Run the main processing function
    extracted_data = preprocess_and_extract_features(SOURCE_FOLDER)
    
    # Save the results to a file
    save_data_to_json(extracted_data, JSON_PATH)