# helpers.py

import os
import torch
import sounddevice as sd
from scipy.io.wavfile import write
from speechbrain.inference.speaker import SpeakerRecognition
from config_jovs import SAMPLE_RATE, CHANNELS, MODEL_SOURCE, MODELS_DIR
import numpy as np
import tkinter as tk
from tkinter import ttk


# --- Model Loading (Singleton) ---
def get_model():
    """Loads and returns the speaker recognition model."""
    global verification_model
    if 'verification_model' not in globals():
        print("Loading verification model KeyVox v1.0")
        run_opts = {
            "device": "cpu",
            "data_parallel_backend": False,
            "local_storage_strategy": "COPY"
        }
        verification_model = SpeakerRecognition.from_hparams(
            source=MODEL_SOURCE,
            savedir=MODELS_DIR,
            run_opts=run_opts
        )
        print("Model loaded.")
    return verification_model


# --- GUI Popup Recorder ---
def record_audio(duration, prompt, gui_mode=False):
    """
    Records audio for a given duration.
    If gui_mode=True, a popup with a progress bar appears while recording.
    Returns None if user cancels.
    """
    popup = None
    cancelled = [False]

    if gui_mode:
        popup = tk.Toplevel()
        popup.title("🎙️ Recording in Progress")
        popup.geometry("400x160")
        popup.configure(bg="#FFF3E0")

        tk.Label(
            popup,
            text=prompt,
            font=("Arial", 11),
            bg="#FFF3E0",
            wraplength=360,
            justify="center"
        ).pack(pady=10)

        progress_var = tk.DoubleVar()
        progress = ttk.Progressbar(popup, length=300, mode='determinate', variable=progress_var)
        progress.pack(pady=5)

        def cancel_recording():
            cancelled[0] = True
            popup.destroy()

        tk.Button(
            popup,
            text="Cancel",
            font=("Arial", 10),
            bg="#FFCDD2",
            command=cancel_recording
        ).pack(pady=5)

        popup.update()
        popup.lift()
        popup.attributes("-topmost", True)

    else:
        print(prompt)
        input("--> Press Enter to start recording...")

    if gui_mode and cancelled[0]:
        return None

    print(f"Recording for {duration} seconds...")
    recording = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='float32'
    )

    # Update progress bar during recording
    if gui_mode:
        total_steps = int(duration * 10)
        for i in range(total_steps):
            if cancelled[0]:
                sd.stop()
                popup.destroy()
                return None
            progress_var.set((i / total_steps) * 100)
            popup.update_idletasks()
            sd.sleep(100)
        progress_var.set(100)

    sd.wait()
    print("✅ Recording stopped.")

    if gui_mode and not cancelled[0]:
        popup.destroy()

    return None if cancelled[0] else recording


def save_temp_audio(recording, filename="temp_audio.wav"):
    """Saves a NumPy audio recording to a temporary file."""
    write(filename, SAMPLE_RATE, recording)
    return filename


def calibrate_ambient_noise(duration=1.0, gui_mode=False):
    """
    Record a short silent sample to estimate background noise level.
    Returns the mean absolute amplitude (ambient level).
    """
    if gui_mode:
        import tkinter.messagebox as messagebox
        messagebox.showinfo("Ambient Calibration", "Please stay quiet for a moment to measure background noise.")

    ambient = record_audio(duration=duration, prompt="Calibrating background noise...", gui_mode=gui_mode)
    if ambient is None:
        return None

    ambient_level = np.mean(np.abs(ambient))
    return ambient_level

# --- Trim leading/trailing quiet frames ---
def trim_silence(signal_tensor, threshold=0.01):
    """
    Trim frames where RMS is below threshold at start and end.
    signal_tensor: [channels, samples]
    """
    signal_np = signal_tensor.numpy()
    rms = np.sqrt(np.mean(signal_np**2, axis=0)) if signal_np.ndim == 1 else np.sqrt(np.mean(signal_np**2, axis=0))
    
    # Find indices above threshold
    indices = np.where(rms > threshold)[0]
    if len(indices) == 0:
        return signal_tensor  # nothing above threshold, return original
    
    start, end = indices[0], indices[-1] + 1
    trimmed_signal = signal_tensor[:, start:end] if signal_tensor.ndim == 2 else signal_tensor[start:end]
    return trimmed_signal


def sliding_windows(signal_tensor, sr, win_sec=1.2, hop_sec=0.6):
    """
    Split [C, T] signal into overlapping [C, Win] segments.
    Returns a list of tensors. Falls back to single full signal if too short.
    """
    x = signal_tensor
    if x.ndim == 1:
        x = x.unsqueeze(0)  # [1, T]
    total = x.shape[-1]
    win = int(win_sec * sr)
    hop = int(hop_sec * sr)
    if total < win:
        return [x]
    starts = list(range(0, total - win + 1, hop))
    segments = [x[:, s:s+win] for s in starts]
    return segments if segments else [x]
