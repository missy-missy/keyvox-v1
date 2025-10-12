  # verify.py

import os
import torch
import torchaudio
import argparse
import numpy as np
from helpers import get_model, record_audio, save_temp_audio
from config import VOICEPRINTS_DIR, SAMPLE_RATE

def main():
    """The main function to handle the verification process."""
    parser = argparse.ArgumentParser(description="Verify a user with their voice.")
    parser.add_argument("username", type=str, help="The username to verify.")
    args = parser.parse_args()
    username = args.username.lower()

    print(f"\n--- Verifying user: {username} ---")

    voiceprint_path = os.path.join(VOICEPRINTS_DIR, f"{username}.pt")
    if not os.path.exists(voiceprint_path):
        print(f"❌ Error: No voiceprint found for '{username}'. Please enroll first.")
        return

    try:
        saved_voiceprint = torch.load(voiceprint_path)
    except Exception as e:
        print(f"❌ Error loading voiceprint: {e}")
        return

    # Loop until a good quality recording is made
    live_recording = None
    while True:
        prompt = "To verify, please say 'My voice is my password' for 4 seconds."
        recording = record_audio(duration=4, prompt=prompt)
        
        rms = np.sqrt(np.mean(recording**2))
        print(f"Recording volume (RMS): {rms:.4f}")
        if rms < 0.01:
            print("❌ Recording seems silent. Please speak louder. Let's try again.\n")
            continue

        min_required_samples = int(1.5 * SAMPLE_RATE)
        if len(recording) < min_required_samples:
            print(f"❌ Recording was too short. Please speak for the full duration. Let's try again.\n")
            continue
            
        live_recording = recording
        break

    temp_file = save_temp_audio(live_recording)

    print("Verifying...")
    model = get_model()

    # --- THIS IS THE FINAL, CORRECTED VERIFICATION LOGIC ---
    # 1. Load the live audio and create an embedding for it
    live_signal, fs = torchaudio.load(temp_file)
    live_embedding = model.encode_batch(live_signal).squeeze()
    
    # 2. similarity() returns only ONE value: a tensor with the score.
    score_tensor = model.similarity(saved_voiceprint, live_embedding)
    
    # 3. Get the Python number from the tensor.
    score = score_tensor.item()
    # --------------------------------------------------------

    print("\n--- Verification Result ---")
    print(f"Similarity Score: {score:.3f}")
    
    custom_threshold = 0.65 

    # 4. Compare the score directly to our threshold.
    if score > custom_threshold:
        print(f"✅ Access Granted. Welcome, {username}!")
    else:
        print("❌ Access Denied. Voice does not match.")
        
    os.remove(temp_file)



if __name__ == "__main__":
    main()