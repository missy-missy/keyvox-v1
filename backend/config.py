
import os

# --- Path Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Central data directory to hold all user-generated content
DATA_DIR = os.path.join(BASE_DIR, "data")

# Specific subdirectory for voiceprints
VOICEPRINTS_DIR = os.path.join(DATA_DIR, "voiceprints")

# Path for the SQLite database file
DATABASE_PATH = os.path.join(DATA_DIR, 'keyvox.db')

# Directory for the downloaded pre-trained model from SpeechBrain
MODELS_DIR = os.path.join(BASE_DIR, "pretrained_models")

# --- Audio Configuration ---
# These variables are required by helpers.py
SAMPLE_RATE = 16000  # The sample rate the SpeechBrain model expects
CHANNELS = 1

# --- Model Configuration ---
# This variable is required by helpers.py
MODEL_SOURCE = "speechbrain/spkrec-ecapa-voxceleb"

# --- Verification Settings ---
# This variable is required by server.py
VERIFICATION_THRESHOLD = 0.75 # The similarity score needed to pass verification.