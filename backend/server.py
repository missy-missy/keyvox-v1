# --- HACK TO MAKE IMPORTS WORK ---
# This block must be at the very top of your entry-point file (server.py)
import sys
import os

# This line adds the parent directory (e.g., 'keyvox') to Python's path
# so it can find the 'backend' package.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# -----------------------------------

from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import torchaudio

# --- CORRECTED IMPORTS ---
# Now that the path is set, use absolute imports from the project root.
from backend import database
from backend.helpers import get_model, perform_quality_checks
from backend.config import VOICEPRINTS_DIR, VERIFICATION_THRESHOLD

# --- Initialization ---
app = Flask(__name__)
CORS(app)

# --- CORRECTED: Initialize DB within app context to prevent race conditions ---
with app.app_context():
    database.init_db()

# Load the SpeechBrain model only once when the server starts
app.model = get_model()

# Create directories for temporary uploads and permanent voiceprints
# Use an absolute path for TEMP_AUDIO_DIR to avoid ambiguity
TEMP_AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_uploads')
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
os.makedirs(VOICEPRINTS_DIR, exist_ok=True)

# --- API Routes ---
@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "ok", "message": "Backend server is running."})

@app.route('/api/register', methods=['POST'])
def register():
    """Handles new user registration."""
    data = request.get_json()
    if not data or not all(k in data for k in ['username', 'full_name', 'email', 'password']):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400

    if database.add_user(data):
        return jsonify({"status": "success", "message": "User registered successfully."}), 201
    else:
        return jsonify({"status": "error", "message": "Username or email already exists."}), 409

@app.route('/api/login', methods=['POST'])
def login():
    """Handles user login with username and password."""
    data = request.get_json()
    username, password = data.get('username'), data.get('password')
    user = database.get_user_by_username(username)
    if user and user['password_hash'] == database.hash_password(password):
        user_details = {k: v for k, v in user.items() if k != 'password_hash'}
        return jsonify({"login_success": True, "user_details": user_details})
    else:
        return jsonify({"login_success": False, "message": "Invalid credentials."}), 401

@app.route('/api/enroll', methods=['POST'])
def enroll():
    """Handles voice enrollment from an uploaded audio file."""
    if 'audio_file' not in request.files or 'username' not in request.form:
        return jsonify({"status": "error", "message": "Missing audio file or username."}), 400

    audio_file = request.files['audio_file']
    username = request.form['username']
    
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, f"enroll_{username}.wav")
    audio_file.save(temp_filepath)
    
    is_good, message = perform_quality_checks(temp_filepath)
    if not is_good:
        os.remove(temp_filepath)
        return jsonify({"status": "error", "message": message}), 400

    try:
        voiceprint_path = os.path.join(VOICEPRINTS_DIR, f"{username.lower()}.pt")
        signal, _ = torchaudio.load(temp_filepath)
        voiceprint = app.model.encode_batch(signal).squeeze()
        torch.save(voiceprint, voiceprint_path)
        database.update_voiceprint_path(username, voiceprint_path)
        
        os.remove(temp_filepath)
        return jsonify({"status": "success", "message": "Voice enrolled successfully."}), 201
    except Exception as e:
        os.remove(temp_filepath)
        print(f"Enrollment Error: {e}")
        return jsonify({"status": "error", "message": "Failed to create voiceprint."}), 500


@app.route('/api/check_enrollment', methods=['POST'])
def check_enrollment():
    """Checks if a user exists and has a valid voiceprint enrolled."""
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({"enrolled": False, "message": "Username not provided."}), 400

    user = database.get_user_by_username(username)
    
    # Check if user exists AND their voiceprint file is physically present
    if user and user.get('voiceprint_path') and os.path.exists(user['voiceprint_path']):
        return jsonify({"enrolled": True})
    else:
        return jsonify({"enrolled": False, "message": "User not found or not enrolled for voice verification."})

@app.route('/api/verify', methods=['POST'])
def verify():
    """Handles voice verification from an uploaded audio file."""
    if 'audio_file' not in request.files or 'username' not in request.form:
        return jsonify({"verified": False, "message": "Missing audio file or username."}), 400

    audio_file = request.files['audio_file']
    username = request.form['username']
    
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, f"verify_{username}.wav")
    audio_file.save(temp_filepath)

    user = database.get_user_by_username(username)
    if not user or not user.get('voiceprint_path') or not os.path.exists(user['voiceprint_path']):
        os.remove(temp_filepath)
        return jsonify({"verified": False, "message": "User is not enrolled for voice verification."})

    try:
        saved_voiceprint = torch.load(user['voiceprint_path'])
        live_signal, _ = torchaudio.load(temp_filepath)
        live_embedding = app.model.encode_batch(live_signal).squeeze()
        
        score_tensor = app.model.similarity(saved_voiceprint, live_embedding)
        score = score_tensor.item()

        os.remove(temp_filepath)

        if score > VERIFICATION_THRESHOLD:
            return jsonify({"verified": True, "score": score, "message": "Access Granted."})
        else:
            return jsonify({"verified": False, "score": score, "message": "Access Denied. Voice does not match."})
    except Exception as e:
        os.remove(temp_filepath)
        print(f"Verification Error: {e}")
        return jsonify({"verified": False, "message": "Error during verification process."}), 500

if __name__ == '__main__':
    if not app.model:
        print("Shutting down due to model loading failure.")
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)