# enroll.py

import os
import torch
import torchaudio
import argparse
import numpy as np
from helpers import get_model, record_audio, save_temp_audio
from config import VOICEPRINTS_DIR, SAMPLE_RATE

def main():
    """The main function to handle the enrollment process."""
    parser = argparse.ArgumentParser(description="Enroll a new user for voice authentication.")
    parser.add_argument("username", type=str, help="The username to enroll.")
    args = parser.parse_args()
    username = args.username.lower()

    print(f"\n--- Enrolling new user: {username} ---")

    os.makedirs(VOICEPRINTS_DIR, exist_ok=True)
    voiceprint_path = os.path.join(VOICEPRINTS_DIR, f"{username}.pt")

    if os.path.exists(voiceprint_path):
        overwrite = input(f"Voiceprint for '{username}' already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("Enrollment cancelled.")
            return

    # --- Loop until a good quality recording is made ---
    enroll_recording = None
    while True:
        prompt = f"Please say 'My voice is my password' clearly for 5 seconds to enroll {username}."
        recording = record_audio(duration=5, prompt=prompt)
        
        # --- Quality Check 1: Volume ---
        rms = np.sqrt(np.mean(recording**2))
        print(f"Recording volume (RMS): {rms:.4f}")
        if rms < 0.01:
            print("❌ Recording seems silent. Please speak louder and closer to the mic. Let's try again.\n")
            continue

        # --- Quality Check 2: Duration ---
        # Require at least 2 seconds of audio data to be safe.
        min_required_samples = int(2.0 * SAMPLE_RATE) 
        if len(recording) < min_required_samples:
            print(f"❌ Recording was too short. Please speak for the entire duration. Let's try again.\n")
            continue

        # If both checks pass, the recording is good.
        enroll_recording = recording
        break

    # --- Proceed with the good recording ---
    temp_file = save_temp_audio(enroll_recording)

    print("Creating voiceprint...")
    model = get_model()
    
    signal, fs = torchaudio.load(temp_file)
    voiceprint = model.encode_batch(signal).squeeze()
    
    torch.save(voiceprint, voiceprint_path)

    print(f"\n✅ Enrollment complete! Voiceprint for '{username}' saved.")
    os.remove(temp_file)

if __name__ == "__main__":
    main()