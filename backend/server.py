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
import speech_recognition as sr
import noisereduce as nr
import soundfile as sf

# --- This allows the server to import from other local files ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Import our custom helpers ---
from helpers import get_voice_embedding
from config import VOICEPRINTS_DIR
from extract_features import preprocess_and_extract_features, save_data_to_json
from visualizer import analyze_lstm_gates

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

# --- SECURITY THRESHOLD & PASSPHRASES ---
SECURITY_THRESHOLD = 0.20
ACCEPTED_PASSPHRASES = [
    "my password is my voice",
    "authenticate me through speech",
    "nine five two seven echo zebra tree",
    "today i confirm my identity using my voice",
    "unlocking access with my voice",
    "my voice is my password"
]

# --- User Data Helper Functions ---
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
# === API ENDPOINTS ===
# ==============================================================================

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "ok"})

@app.route('/api/register', methods=['POST'])
def register():
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
    username = request.form['username'].lower()
    audio_file = request.files['audio_file']
    users = read_users()
    if username not in users:
        return jsonify({"status": "error", "message": "User not found."}), 404
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, f"enroll_{username}.wav")
    audio_file.save(temp_filepath)
    try:
        voice_embedding = get_voice_embedding(temp_filepath)
        if voice_embedding is None:
            return jsonify({"status": "error", "message": "Could not process audio file. It might be too short or silent."}), 400
        voiceprint_filename = f"{username}.npy"
        absolute_voiceprint_path = os.path.join(VOICEPRINTS_DIR, voiceprint_filename)
        np.save(absolute_voiceprint_path, voice_embedding)
        relative_voiceprint_path = os.path.join("voiceprints", voiceprint_filename)
        users[username]['voiceprint_path'] = relative_voiceprint_path
        write_users(users)
        
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
    username = request.get_json()['username'].lower()
    user = read_users().get(username)
    if user and user.get('voiceprint_path') and os.path.exists(user['voiceprint_path']):
        return jsonify({"enrolled": True})
    return jsonify({"enrolled": False, "message": "User not found or voice not enrolled."})

@app.route('/api/verify_voice', methods=['POST'])
def verify_voice():
    username = request.form['username'].lower()
    audio_file = request.files['audio_file']
    user = read_users().get(username)
    
    temp_filepath = None
    cleaned_filepath = None

    if not user or not user.get('voiceprint_path'):
        return jsonify({"verified": False, "message": "User or voiceprint not found."})
    
    stored_voiceprint_path = user['voiceprint_path']
    if not os.path.exists(stored_voiceprint_path):
        return jsonify({"verified": False, "message": "Stored voiceprint file is missing."})
        
    try:
        temp_filepath = os.path.join(TEMP_AUDIO_DIR, f"verify_{username}.wav")
        audio_file.save(temp_filepath)
        
        print(f"--- [VERIFY CHECK 1] Running Speaker Verification for {username} ---")
        live_embedding = get_voice_embedding(temp_filepath)
        if live_embedding is None:
            return jsonify({"verified": False, "message": "Could not process live audio for speaker verification."})
        stored_embedding = np.load(stored_voiceprint_path)
        distance = cosine(stored_embedding, live_embedding)
        print(f"Voice similarity distance: {distance:.4f} (Threshold: < {SECURITY_THRESHOLD})")
        if distance >= SECURITY_THRESHOLD:
            return jsonify({"verified": False, "message": "Voice does not match."})

        # --- MODIFICATION: PASSPHRASE CHECK REMOVED ---
        # If the code reaches here, the voice similarity check passed.
        # We now return a success message immediately.
        print("--- [VERIFY CHECK 2] Passphrase check skipped. Verification successful. ---")
        return jsonify({"verified": True})

        # ======================================================================
        # === The original passphrase check code below is now commented out ===
        # ======================================================================

        # print("--- [PRE-CHECK 2] Applying noise reduction to audio ---")
        # audio_data, sample_rate = sf.read(temp_filepath)
        # reduced_noise_audio = nr.reduce_noise(y=audio_data, sr=sample_rate)
        # cleaned_filepath = os.path.join(TEMP_AUDIO_DIR, f"verify_{username}_cleaned.wav")
        # sf.write(cleaned_filepath, reduced_noise_audio, sample_rate)

        # print(f"--- [VERIFY CHECK 2] Running Speech Recognition for passphrase check ---")
        # recognizer = sr.Recognizer()
        # with sr.AudioFile(cleaned_filepath) as source:
        #     audio_for_transcription = recognizer.record(source)
        
        # # --- THIS IS THE CORRECTED AND COMPLETE TRY/EXCEPT BLOCK ---
        # try:
        #     transcribed_text = recognizer.recognize_whisper(audio_for_transcription, language="english", model="base")
        #     cleaned_text = ''.join(c for c in transcribed_text.lower() if c.isalpha() or c.isspace()).strip()
        #     print(f"Transcribed Text: '{cleaned_text}'")
            
        #     if cleaned_text in ACCEPTED_PASSPHRASES:
        #         print("Passphrase match found.")
        #         return jsonify({"verified": True})
        #     else:
        #         print("Passphrase does not match.")
        #         return jsonify({"verified": False, "message": "Incorrect or unclear passphrase spoken."})

        # except sr.UnknownValueError:
        #     return jsonify({"verified": False, "message": "Could not understand audio. Please speak clearly."})
        # except sr.RequestError:
        #     return jsonify({"verified": False, "message": "Speech recognition service error."})
        # # --- END OF CORRECTED BLOCK ---
            
    except Exception as e:
        return jsonify({"verified": False, "message": f"An unexpected error occurred: {str(e)}"})
    finally:
        if temp_filepath and os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        if cleaned_filepath and os.path.exists(cleaned_filepath):
            os.remove(cleaned_filepath)
            
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username, password = data['username'].lower(), data['password']
    user = read_users().get(username)
    if user and user['password_hash'] == hash_password(password):
        user_details = {k: v for k, v in user.items() if k != 'password_hash'}
        return jsonify({"login_success": True, "user_details": user_details})
    return jsonify({"login_success": False, "message": "Invalid credentials."})

@app.route('/api/visualize_gates', methods=['POST'])
def visualize_gates():
    if 'audio_file' not in request.files: return jsonify({"error": "No audio file provided."}), 400
    audio_file = request.files['audio_file']
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, "live_demo.wav")
    audio_file.save(temp_filepath)
    try:
        gate_data = analyze_lstm_gates(temp_filepath)
        if "error" in gate_data: return jsonify(gate_data), 400
        return jsonify(gate_data)
    except Exception as e:
        return jsonify({"error": f"Visualization failed: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

# --- Main Execution Block ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)