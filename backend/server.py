import os
import sys
import json
import shutil  # For file operations like copying
import hashlib # For securely hashing passwords
from datetime import datetime

# --- Third-Party Libraries ---
import torch
import torchaudio
from flask import Flask, request, jsonify
from flask_cors import CORS # To allow the frontend to communicate with this server

# --- This allows the server to import from your original, unchanged prototype files ---
# It adds the current directory ('backend/') to Python's system path.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Direct imports from YOUR original prototype files ---
# We are treating your prototype scripts as libraries for our server.
from helpers import get_model
from config import VOICEPRINTS_DIR
from extract_features import preprocess_and_extract_features, save_data_to_json

# --- Flask App Initialization ---
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing to prevent browser errors when the
# frontend (on a different "origin") calls the backend.
CORS(app)

# --- Global Path and Configuration Setup ---
# Define paths for generated files and folders.
USER_DB_PATH = os.path.join(os.path.dirname(__file__), 'users.json')
TEMP_AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'temp_uploads')
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), 'recordings') # For the extract_features.py pipeline

# Ensure all necessary directories exist when the server starts up.
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
os.makedirs(VOICEPRINTS_DIR, exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# --- Load the SpeechBrain Model on Startup ---
# We load the model only once when the server starts. This is highly efficient,
# as it prevents the long loading time on every API request.
# The model is stored in `app.model` to be accessible in all API routes.
print("Server is starting, loading model via helpers.py...")
app.model = get_model()

# --- User Data Helper Functions (using users.json as a simple database) ---

def read_users():
    """Reads the entire users.json file and returns it as a Python dictionary."""
    if not os.path.exists(USER_DB_PATH): return {}
    with open(USER_DB_PATH, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError: # Handles case where the file is empty or corrupt
            return {}

def write_users(data):
    """Writes a Python dictionary back to the users.json file with pretty formatting."""
    with open(USER_DB_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    """Hashes a plain-text password using SHA256 for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

# ==============================================================================
# === API ENDPOINTS (The connection between your frontend and backend logic) ===
# ==============================================================================

@app.route('/api/status', methods=['GET'])
def status():
    """A simple endpoint for the frontend to check if the server is online."""
    return jsonify({"status": "ok"})

@app.route('/api/register', methods=['POST'])
def register():
    """
    Handles Step 1 of the UI's enrollment flow.
    Receives user details (name, email, password) and saves them to users.json.
    """
    data = request.get_json()
    users = read_users()
    username = data['username'].lower()

    # Check if the username is already taken.
    if username in users:
        return jsonify({"status": "error", "message": "Username already exists."}), 409
    
    # Create a new user entry with a hashed password.
    users[username] = {
        "full_name": data['full_name'],
        "email": data['email'],
        "password_hash": hash_password(data['password']),
        "voiceprint_path": None # The voiceprint will be added in the next step.
    }
    write_users(users)
    
    return jsonify({"status": "success", "message": "User registered. Proceed to voice enrollment."})

@app.route('/api/enroll_voice', methods=['POST'])
def enroll_voice():
    """
    Handles the voice recording step of the UI's enrollment flow.
    This is the core endpoint that performs BOTH authentication and data collection.
    """
    username = request.form['username'].lower()
    audio_file = request.files['audio_file']
    users = read_users()

    # Ensure the user was registered in Step 1.
    if username not in users:
        return jsonify({"status": "error", "message": "User not found."}), 404
    
    # Save the uploaded audio to a temporary file for processing.
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, f"enroll_{username}.wav")
    audio_file.save(temp_filepath)
    
    try:
        # --- TASK A: AUTHENTICATION (Using SpeechBrain logic from helpers.py/enroll.py) ---
        print(f"--- [AUTH] Creating SpeechBrain voiceprint for {username} ---")
        signal, _ = torchaudio.load(temp_filepath)

        # Protective check: Ensure the audio is long enough for the model to process.
        MIN_SAMPLES = 4000
        if signal.shape[1] < MIN_SAMPLES:
            return jsonify({
                "status": "error",
                "message": "Processing failed: The recording was too short or silent. Please try again."
            }), 400
       
        # Create the secure voiceprint using the loaded SpeechBrain model.
        voiceprint = app.model.encode_batch(signal).squeeze()
        
        # Save the voiceprint to the voiceprints folder.
        voiceprint_path = os.path.join(VOICEPRINTS_DIR, f"{username}.pt")
        torch.save(voiceprint, voiceprint_path)
        
        # Update the user's record in users.json to link to their new voiceprint.
        users[username]['voiceprint_path'] = voiceprint_path
        write_users(users)

        # --- TASK B: DATA COLLECTION (Using your original extract_features.py logic) ---
        print(f"--- [DATA] Running MFCC feature extraction pipeline ---")
        # 1. Copy the enrollment audio to the permanent 'recordings' folder.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        permanent_audio_path = os.path.join(RECORDINGS_DIR, f"{username}_enroll_{timestamp}.wav")
        shutil.copy(temp_filepath, permanent_audio_path)
        
        # 2. Call the functions directly from your extract_features.py script.
        json_path = os.path.join(os.path.dirname(__file__), "data_features.json")
        extracted_data = preprocess_and_extract_features(RECORDINGS_DIR) # Processes the entire folder
        save_data_to_json(extracted_data, json_path) # Overwrites the JSON file with updated features

        return jsonify({"status": "success", "message": "Voice enrolled and data collected."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Processing failed: {str(e)}"}), 500
    finally:
        # Always clean up the temporary file, even if an error occurred.
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

@app.route('/api/check_enrollment', methods=['POST'])
def check_enrollment():
    """Powers the username entry screen in the login flow. Checks if a user exists and has a voiceprint."""
    username = request.get_json()['username'].lower()
    user = read_users().get(username)
    # The check is robust: the user must exist AND the voiceprint file must physically be on the disk.
    if user and user.get('voiceprint_path') and os.path.exists(user['voiceprint_path']):
        return jsonify({"enrolled": True})
    return jsonify({"enrolled": False, "message": "User not found or voice not enrolled."})

@app.route('/api/verify_voice', methods=['POST'])
def verify_voice():
    """Handles the voice verification step of the login flow."""
    username = request.form['username'].lower()
    audio_file = request.files['audio_file']
    user = read_users().get(username)

    if not user or not user.get('voiceprint_path'):
        return jsonify({"verified": False, "message": "User or voiceprint not found."})
    
    voiceprint_to_check = user['voiceprint_path']
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, f"verify_{username}.wav")
    audio_file.save(temp_filepath)
    
    try:
        # Load the user's stored voiceprint.
        saved_voiceprint = torch.load(voiceprint_to_check)
        live_signal, _ = torchaudio.load(temp_filepath)

        # Protective check for the live audio sample.
        MIN_SAMPLES = 4000
        if live_signal.shape[1] < MIN_SAMPLES:
            return jsonify({
                "verified": False,
                "message": "Verification failed: The recording was too short or silent. Please try again."
            }), 400
  
        # Use the SpeechBrain model to create a voiceprint from the live audio...
        live_embedding = app.model.encode_batch(live_signal).squeeze()
        # ...and compare it to the stored one.
        score_tensor = app.model.similarity(saved_voiceprint, live_embedding)
        score = score_tensor.item()

        os.remove(temp_filepath)
        
        # Compare the similarity score against our security threshold.
        if score > 0.65:
            return jsonify({"verified": True})
        else:
            return jsonify({"verified": False, "message": "Voice does not match."})
    except Exception as e:
        if os.path.exists(temp_filepath): os.remove(temp_filepath)
        return jsonify({"verified": False, "message": f"Verification error: {str(e)}"})

@app.route('/api/login', methods=['POST'])
def login():
    """Handles the final password check of the login flow."""
    data = request.get_json()
    username, password = data['username'].lower(), data['password']
    user = read_users().get(username)

    # Compare the hashed password from the request with the stored hashed password.
    if user and user['password_hash'] == hash_password(password):
        # On success, send user details back to the frontend (excluding the password hash).
        user_details = {k: v for k, v in user.items() if k != 'password_hash'}
        return jsonify({"login_success": True, "user_details": user_details})
    
    return jsonify({"login_success": False, "message": "Invalid credentials."})

# --- Main Execution Block ---
if __name__ == '__main__':
    """This block runs only when you execute 'python server.py' directly."""
    # The host='0.0.0.0' makes the server accessible from your local network.
    # The debug=True provides helpful error messages in the terminal during development.
    app.run(host='0.0.0.0', port=5000, debug=True)