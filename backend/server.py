import os
import sys
import json
import shutil
import hashlib
from datetime import datetime

# --- Third-Party Libraries ---
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from scipy.spatial.distance import cosine

# --- This allows the server to import from other local files ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Import our new custom helper and the original data collection logic ---
from helpers import get_voice_embedding
from config import VOICEPRINTS_DIR
from extract_features import preprocess_and_extract_features, save_data_to_json

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- Global Path and Configuration Setup ---
USER_DB_PATH = os.path.join(os.path.dirname(__file__), 'users.json')
TEMP_AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'temp_uploads')
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), 'recordings')

os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
os.makedirs(VOICEPRINTS_DIR, exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# --- SECURITY THRESHOLD ---
# This number comes from your 2_Biometric_Evaluation.ipynb notebook.
# It's the point where your Equal Error Rate (EER) occurred.
# For cosine distance, a smaller number means more similar. A lower threshold is more secure.
# Let's start with a reasonably secure value. You can adjust this after testing.
SECURITY_THRESHOLD = 0.35

# --- User Data Helper Functions (Unchanged) ---
def read_users():
    if not os.path.exists(USER_DB_PATH): return {}
    with open(USER_DB_PATH, 'r') as f:
        try: return json.load(f)
        except json.JSONDecodeError: return {}

def write_users(data):
    with open(USER_DB_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==============================================================================
# === API ENDPOINTS (with new model logic) ===
# ==============================================================================

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "ok"})

@app.route('/api/register', methods=['POST'])
def register():
    # This endpoint's logic is unchanged.
    data = request.get_json()
    users = read_users()
    username = data['username'].lower()
    if username in users:
        return jsonify({"status": "error", "message": "Username already exists."}), 409
    users[username] = {
        "full_name": data['full_name'],
        "email": data['email'],
        "password_hash": hash_password(data['password']),
        "voiceprint_path": None
    }
    write_users(users)
    return jsonify({"status": "success", "message": "User registered. Proceed to voice enrollment."})

@app.route('/api/enroll_voice', methods=['POST'])
def enroll_voice():
    """
    Handles voice enrollment using the new LSTM embedding model.
    """
    username = request.form['username'].lower()
    audio_file = request.files['audio_file']
    users = read_users()

    if username not in users:
        return jsonify({"status": "error", "message": "User not found."}), 404
    
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, f"enroll_{username}.wav")
    audio_file.save(temp_filepath)
    
    try:
        # --- TASK A: AUTHENTICATION (Create voiceprint with new model) ---
        print(f"--- [ENROLL] Creating voice embedding for {username} ---")
        voice_embedding = get_voice_embedding(temp_filepath)

        if voice_embedding is None:
            return jsonify({"status": "error", "message": "Could not process audio file. It might be too short or silent."}), 400

        # Save the voiceprint as a standard .npy file
        voiceprint_filename = f"{username}.npy"
        voiceprint_path = os.path.join(VOICEPRINTS_DIR, voiceprint_filename)
        np.save(voiceprint_path, voice_embedding)
        
        # Update users.json with the path to the new voiceprint
        users[username]['voiceprint_path'] = voiceprint_path
        write_users(users)

        # --- TASK B: DATA COLLECTION (Your original logic, unchanged) ---
        print(f"--- [DATA] Running MFCC feature extraction pipeline for data collection ---")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        permanent_audio_path = os.path.join(RECORDINGS_DIR, f"{username}_enroll_{timestamp}.wav")
        shutil.copy(temp_filepath, permanent_audio_path)
        
        json_path = os.path.join(os.path.dirname(__file__), "data_features.json")
        extracted_data = preprocess_and_extract_features(RECORDINGS_DIR)
        save_data_to_json(extracted_data, json_path)

        return jsonify({"status": "success", "message": "Voice enrolled and data collected."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Enrollment failed: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

@app.route('/api/check_enrollment', methods=['POST'])
def check_enrollment():
    # This endpoint's logic is unchanged.
    username = request.get_json()['username'].lower()
    user = read_users().get(username)
    if user and user.get('voiceprint_path') and os.path.exists(user['voiceprint_path']):
        return jsonify({"enrolled": True})
    return jsonify({"enrolled": False, "message": "User not found or voice not enrolled."})

@app.route('/api/verify_voice', methods=['POST'])
def verify_voice():
    """
    Handles voice verification using the new LSTM model and cosine similarity.
    """
    username = request.form['username'].lower()
    audio_file = request.files['audio_file']
    user = read_users().get(username)

    if not user or not user.get('voiceprint_path'):
        return jsonify({"verified": False, "message": "User or voiceprint not found."})
    
    stored_voiceprint_path = user['voiceprint_path']
    if not os.path.exists(stored_voiceprint_path):
        return jsonify({"verified": False, "message": "Stored voiceprint file is missing."})
        
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, f"verify_{username}.wav")
    audio_file.save(temp_filepath)
    
    try:
        # 1. Get embedding for the LIVE audio from the request
        live_embedding = get_voice_embedding(temp_filepath)
        
        if live_embedding is None:
            return jsonify({"verified": False, "message": "Could not process live audio. It might be too short or silent."})
            
        # 2. Load the STORED embedding from the user's enrollment
        stored_embedding = np.load(stored_voiceprint_path)

        print(f"DEBUG: Shape of LIVE embedding: {live_embedding.shape}")
        print(f"DEBUG: Shape of STORED embedding: {stored_embedding.shape}")
        
        # 3. Calculate the cosine distance between the two voiceprints.
        #    A score of 0.0 means they are identical. A score of 1.0 means they are very different.
        distance = cosine(stored_embedding, live_embedding)
        
        print(f"--- [VERIFY] Voice similarity distance for {username}: {distance:.4f} (Threshold: < {SECURITY_THRESHOLD})")
        
        # 4. Compare the distance to our security threshold.
        #    If the distance is LESS than the threshold, the voices are a match.
        if distance < SECURITY_THRESHOLD:
            return jsonify({"verified": True})
        else:
            return jsonify({"verified": False, "message": "Voice does not match."})
            
    except Exception as e:
        return jsonify({"verified": False, "message": f"Verification error: {str(e)}"})
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

@app.route('/api/login', methods=['POST'])
def login():
    # This endpoint's logic is unchanged.
    data = request.get_json()
    username, password = data['username'].lower(), data['password']
    user = read_users().get(username)
    if user and user['password_hash'] == hash_password(password):
        user_details = {k: v for k, v in user.items() if k != 'password_hash'}
        return jsonify({"login_success": True, "user_details": user_details})
    return jsonify({"login_success": False, "message": "Invalid credentials."})

# --- Main Execution Block ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)