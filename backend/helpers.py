import torch
import torchaudio
import numpy as np
from speechbrain.inference.speaker import SpeakerRecognition
from backend.config import SAMPLE_RATE, MODEL_SOURCE, MODELS_DIR

def get_model():
    """
    Loads and returns the pre-trained SpeechBrain speaker recognition model.
    This function should only be called once when the server starts.
    """
    print("Loading SpeechBrain model (this may take a moment on first run)...")
    try:
        # Using run_opts to specify CPU and a safe data copy strategy
        run_opts = {"device": "cpu", "data_parallel_backend": False, "local_storage_strategy": "COPY"}
        model = SpeakerRecognition.from_hparams(
            source=MODEL_SOURCE, 
            savedir=MODELS_DIR,
            run_opts=run_opts
        )
        print("✅ SpeechBrain model loaded successfully.")
        return model
    except Exception as e:
        print(f"❌ Critical Error: Could not load SpeechBrain model: {e}")
        return None

def perform_quality_checks(audio_filepath):
    """
    Performs volume and duration checks on a received audio file.
    This logic is taken directly from your original `enroll.py` script.
    
    :param audio_filepath: Path to the temporary audio file.
    :return: A tuple (is_good_quality, message).
    """
    try:
        signal, fs = torchaudio.load(audio_filepath)
        
        # Resample audio if the frontend sent a different sample rate (e.g., 44.1k)
        if fs != SAMPLE_RATE:
            print(f"Resampling audio from {fs}Hz to {SAMPLE_RATE}Hz...")
            resampler = torchaudio.transforms.Resample(orig_freq=fs, new_freq=SAMPLE_RATE)
            signal = resampler(signal)

        # Quality Check 1: Volume (RMS)
        rms = np.sqrt(np.mean(signal.numpy()**2))
        print(f"Recording volume (RMS): {rms:.4f}")
        if rms < 0.01:
            return (False, "Recording is too silent. Please speak louder and try again.")
            
        # Quality Check 2: Duration
        min_samples = int(2.0 * SAMPLE_RATE) # Require at least 2 seconds
        if signal.shape[1] < min_samples:
            return (False, "Recording is too short. Please speak for the full duration.")

        return (True, "Audio quality is good.")
    except Exception as e:
        print(f"Error during audio quality check: {e}")
        return (False, "Could not process the provided audio file.")