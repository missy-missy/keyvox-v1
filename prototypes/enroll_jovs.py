# enrolls.py

import os
import torch
import torchaudio
import numpy as np
import warnings
import contextlib
import sys
import sounddevice as sd
from helpers_jovs import get_model, record_audio, save_temp_audio, calibrate_ambient_noise, trim_silence, sliding_windows
from config_jovs import VOICEPRINTS_DIR, SAMPLE_RATE, DURATION

import tkinter as tk
from tkinter import messagebox

# --- Suppress noisy logs ---
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")


@contextlib.contextmanager
def suppress_stdout():
    """Hide backend prints temporarily."""
    with open(os.devnull, "w") as fnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = fnull, fnull
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr


def enroll_user(username: str) -> bool:
    """
    Enroll a user for voice authentication.
    Always GUI-based.
    """
    username = username.lower()
    root = tk.Tk()
    root.withdraw()  # hide main window

    os.makedirs(VOICEPRINTS_DIR, exist_ok=True)
    voiceprint_path = os.path.join(VOICEPRINTS_DIR, f"{username}.pt")

    # --- Check if voiceprint already exists ---
    if os.path.exists(voiceprint_path):
        overwrite = messagebox.askyesno(
            "Overwrite Existing Voiceprint",
            f"A voiceprint for '{username}' already exists.\nDo you want to overwrite it?"
        )
        if not overwrite:
            messagebox.showinfo(
                "Enrollment Cancelled",
                "Enrollment cancelled. Existing voiceprint was kept."
            )
            root.destroy()
            return False
        # If user chooses Yes, continue and overwrite

    ambient_level = calibrate_ambient_noise(gui_mode=True)
    if ambient_level is None:
        messagebox.showwarning("Calibration Cancelled", "Ambient noise calibration was cancelled.")
        root.destroy()
        return False

    # --- Recording loop ---
    while True:
        # UPDATED PHRASE (display only)
        prompt_msg = (
            f"-----------------------------------------------\n\n"
            f"“My voice is my password; please grant access to my account.”"
            f"\n\n-----------------------------------------------\n\n"
            f"Press 'OK' to begin recording."
        )
        messagebox.showinfo(f"You have {DURATION} secs. Say the phrase clearly {username.upper()}!", prompt_msg)

        recording = record_audio(
            duration=DURATION,
            # UPDATED PHRASE (recording prompt)
            prompt=f"“My voice is my password; Please grant access\n\tto my account.”\n\n Please say the phrase clearly for {DURATION} seconds.",
            gui_mode=True
        )

        # SAFETY: check cancellation BEFORE normalization
        if recording is None:
            messagebox.showwarning("Enrollment Cancelled", "Recording was cancelled.")
            root.destroy()
            return False

        # Normalize amplitude to ensure consistent loudness
        recording = recording / (np.max(np.abs(recording)) + 1e-6)

        rms = np.sqrt(np.mean(recording**2))
        if rms < 0.01:
            messagebox.showwarning("Low Volume", "Recording seems silent. Please speak louder and closer to the mic.")
            continue

        # Normalize loudness using RMS
        target_rms = 0.05  # desired consistent loudness
        recording = recording * (target_rms / (rms + 1e-6))

        min_required_samples = int(2.0 * SAMPLE_RATE)
        if len(recording) < min_required_samples:
            messagebox.showwarning("Short Recording", "Recording was too short. Please speak for the entire duration.")
            continue

        # --- Adaptive background noise / silence check ---
        noise_level = np.mean(np.abs(recording[:int(0.5 * SAMPLE_RATE)]))
        rms = np.sqrt(np.mean(recording**2))
        threshold = max(ambient_level * 4.0, 0.04)  # slightly higher floor

        # Case 1: Too loud (background noise)
        # Case 2: Too quiet (nobody spoke)
        if noise_level > threshold or rms < 0.01:
            if rms < 0.01:
                msg = (
                    "It seems no one is speaking.\n\n"
                    "Please speak clearly into the microphone for the recording."
                )
                messagebox.showinfo("Enrollment Cancelled", msg)
                continue  # loop back to re-record
            else:
                msg = (
                    f"Background noise is too strong.\n\n"
                    f"Measured: {noise_level:.4f}\n"
                    f"Threshold: {threshold:.4f}\n\n"
                    "You can continue, but this may affect enrollment accuracy.\n"
                    "Do you want to proceed anyway?"
                )
                proceed = messagebox.askyesno("Noisy Environment", msg)
                if not proceed:
                    messagebox.showinfo("Enrollment Cancelled", "Please move to a quieter place and try again.")
                    continue  # loop back to re-record

        # --- Optionally let the user listen to their recording ---
        temp_file = save_temp_audio(recording)
        playback_choice = messagebox.askyesno(
            "Playback Option",
            "Would you like to listen to your recording before continuing?"
        )

        if playback_choice:
            import time
            import threading

            play_window = tk.Toplevel()
            play_window.title("Playback")
            play_window.geometry("300x100")
            tk.Label(play_window, text="🔊 Playing your recorded voice...", font=("Segoe UI", 11)).pack(pady=20)

            def play_and_close():
                sd.play(recording, SAMPLE_RATE)
                sd.wait()
                time.sleep(0.3)
                play_window.destroy()

            threading.Thread(target=play_and_close, daemon=True).start()

            # Keep UI responsive while waiting
            while play_window.winfo_exists():
                play_window.update()
                time.sleep(0.05)

        # Ask for confirmation before proceeding
        confirm = messagebox.askyesno(
            "Confirm Recording",
            "Do you want to use this recording for enrollment?"
        )
        if not confirm:
            messagebox.showinfo("Re-record", "Let's try again.")
            continue  # loop back to re-record
        break

    # messagebox.showinfo("Processing", "Creating your voiceprint, please wait...")

    with suppress_stdout():
        model = get_model()

    signal, fs = torchaudio.load(temp_file)
    if fs != SAMPLE_RATE:
        import torchaudio.functional as AF
        signal = AF.resample(signal, fs, SAMPLE_RATE)

    # --- Trim leading/trailing quiet frames (gentler) ---
    signal = trim_silence(signal, threshold=0.005)

    # --- Segmented enrollment to MATCH verification ---
    segments = sliding_windows(signal, SAMPLE_RATE, win_sec=1.5, hop_sec=0.5)
    embeds = []
    with torch.no_grad():
        for seg in segments:
            # skip very short segments
            if seg.shape[-1] < int(0.6 * SAMPLE_RATE):
                continue
            emb = model.encode_batch(seg)
            # Remove batch dim if present
            if emb.ndim == 3:  # [1, frames, dim]
                emb = emb.squeeze(0)
            # Average across frames (temporal mean)
            if emb.ndim == 2:  # [frames, dim]
                emb = emb.mean(dim=0)
            # L2 normalize per-segment
            emb = emb / (emb.norm(p=2) + 1e-8)
            embeds.append(emb)

    if not embeds:
        messagebox.showerror("Enrollment Error", "Recording too short/noisy. Please try again.")
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        root.destroy()
        return False

    # Aggregate segments (mean, matching verify)
    voiceprint = torch.stack(embeds, dim=0).mean(dim=0)
    voiceprint = voiceprint / (voiceprint.norm(p=2) + 1e-8)
    torch.save(voiceprint, voiceprint_path)

    print("Temp file path:", temp_file)
    if temp_file and os.path.exists(temp_file):
        os.remove(temp_file)

    # --- Show exact save location to the user ---
    messagebox.showinfo(
        "Enrollment Success",
        f"✅ Enrollment complete!\nVoiceprint for '{username}' saved at:\n{os.path.abspath(voiceprint_path)}"
    )
    root.destroy()
    return True
