import os
import torch
import sounddevice as sd
from scipy.io.wavfile import write
from speechbrain.inference.speaker import SpeakerRecognition

# Import only the necessary settings from our central config file
from config import SAMPLE_RATE, CHANNELS, MODEL_SOURCE, MODELS_DIR

# --- Model Loading (Singleton) ---
def get_model():
    """Loads and returns the speaker recognition model."""
    global verification_model
    if 'verification_model' not in globals():
        print("Loading SpeechBrain model (this may take a moment on first run)...")
        
        # The definitive solution: Use 'run_opts' to specify the copy strategy.
        run_opts = {"device": "cpu", "data_parallel_backend": False, "local_storage_strategy": "COPY"}
        
        verification_model = SpeakerRecognition.from_hparams(
            source=MODEL_SOURCE, 
            savedir=MODELS_DIR,
            run_opts=run_opts
        )
        print("Model loaded.")
    return verification_model

# --- Shared Functions ---
def record_audio(duration, prompt):
    """Waits for the user to press Enter, then records audio."""
    print(prompt)
    input("--> Press Enter to start recording...")

    print(f"Recording for {duration} seconds...")
    recording = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32')
    sd.wait()
    
    print("Recording stopped.")
    return recording

def save_temp_audio(recording, filename="temp_audio.wav"):
    """Saves a NumPy audio recording to a temporary file."""
    write(filename, SAMPLE_RATE, recording)
    return filename