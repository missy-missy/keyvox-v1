# config.py
# This file contains all configuration variables and path management for the project.

import os

# --- Path Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VOICEPRINTS_FOLDER_NAME = "voiceprints"
MODELS_FOLDER_NAME = "pretrained_models"

VOICEPRINTS_DIR = os.path.join(BASE_DIR, VOICEPRINTS_FOLDER_NAME)
MODELS_DIR = os.path.join(BASE_DIR, MODELS_FOLDER_NAME)

# --- Audio Configuration ---
SAMPLE_RATE = 16000
CHANNELS = 1

# --- Model Configuration ---
MODEL_SOURCE = "speechbrain/spkrec-ecapa-voxceleb"

# --- Recording Configuration ---
DURATION = 5

# --- Verification Configuration ---
VERIFICATION_THRESHOLD = 0.68
