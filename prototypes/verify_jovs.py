# verify.py

import os
import torch
import torchaudio
import numpy as np
import warnings
import contextlib
import sys
from helpers_jovs import get_model, record_audio, save_temp_audio,  trim_silence, sliding_windows
from config_jovs import VOICEPRINTS_DIR, SAMPLE_RATE, DURATION, VERIFICATION_THRESHOLD

import tkinter as tk
from tkinter import messagebox

# --- Hide backend noise ---
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"
warnings.filterwarnings("ignore")


@contextlib.contextmanager
def suppress_stdout():
    """Suppress backend prints."""
    with open(os.devnull, "w") as fnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = fnull, fnull
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

def load_cohort(voiceprints_dir, exclude_username):
    cohort = []
    for fname in os.listdir(voiceprints_dir):
        if not fname.endswith(".pt"):
            continue
        if fname == f"{exclude_username}.pt":
            continue
        v = torch.load(os.path.join(voiceprints_dir, fname))
        if v.ndim == 2:
            v = v.mean(dim=0)
        v = v / (v.norm(p=2) + 1e-8)
        cohort.append(v)
    return cohort

def verify_user(username: str) -> bool:
    """
    Verify a user by comparing their voiceprint.
    Always GUI-based.
    """
    username = username.lower()
    root = tk.Tk()
    root.withdraw()  # hide main window

    voiceprint_path = os.path.join(VOICEPRINTS_DIR, f"{username}.pt")
    if not os.path.exists(voiceprint_path):
        # fix typo in path earlier (ensure correct path string)
        voiceprint_path = os.path.join(VOICEPRINTS_DIR, f"{username}.pt")
    if not os.path.exists(voiceprint_path):
        messagebox.showerror("Verification Error", f"No enrollment found for '{username}'.")
        root.destroy()
        return False

    # Phrase already updated to your new 5s text.
    prompt_msg = f"Please say 'My voice is my password; please grant access to my account.' clearly for {DURATION} seconds to verify."
    messagebox.showinfo("Verification Prompt", prompt_msg)

    recording = record_audio(duration=DURATION, prompt=prompt_msg, gui_mode=True)
    if recording is None:
        messagebox.showwarning("Verification Cancelled", "Recording was cancelled.")
        root.destroy()
        return False
    
    # Peak normalize only (avoid RMS forcing which can alter SNR)
    peak = float(np.max(np.abs(recording)) + 1e-6)
    recording = recording / peak

    # Low-volume sanity check (after peak-norm this still catches near-silence)
    rms = float(np.sqrt(np.mean(recording**2)))
    if rms < 0.01:
        messagebox.showwarning("Low Volume", "Recording seems silent. Please speak louder and closer to the mic.")
        root.destroy()
        return False

    temp_file = save_temp_audio(recording)

    with suppress_stdout():
        model = get_model()

    signal, fs = torchaudio.load(temp_file)
    # --- Trim leading/trailing quiet frames (match enroll) ---
    signal = trim_silence(signal, threshold=0.005)
    # Diagnostics: how much speech survived trimming?
    secs = float(signal.shape[-1]) / SAMPLE_RATE
    print(f"[DEBUG] trimmed_len_sec={secs:.2f}")
    if secs < 0.8:
        print("[WARN] Very short effective speech after trimming; results may be unstable.")




    if temp_file and os.path.exists(temp_file):
        os.remove(temp_file)

    # (Optional) Resample to match model/sample rate
    if fs != SAMPLE_RATE:
        import torchaudio.functional as AF
        signal = AF.resample(signal, fs, SAMPLE_RATE)
        fs = SAMPLE_RATE

    # --- Load stored embedding (target) once ---
    stored_embedding = torch.load(voiceprint_path)
    if stored_embedding.ndim == 2:
        stored_embedding = stored_embedding.mean(dim=0)
    stored_embedding = stored_embedding / (stored_embedding.norm(p=2) + 1e-8)

    # ---------- Primary: full-utterance embedding ----------
    with torch.no_grad():
        full_emb = model.encode_batch(signal)
    if full_emb.ndim == 3:
        full_emb = full_emb.squeeze(0)
    if full_emb.ndim == 2:
        full_emb = full_emb.mean(dim=0)
    full_emb = full_emb / (full_emb.norm(p=2) + 1e-8)

    full_cos = torch.nn.functional.cosine_similarity(
        full_emb.unsqueeze(0), stored_embedding.unsqueeze(0), dim=1
    ).item()

    # ---------- Stabilizer: multi-segment Top-K median ----------
    segments = sliding_windows(signal, fs, win_sec=1.5, hop_sec=0.5)
    # cap segments to avoid tails
    segments = segments[:8]

    # Keep only the most voiced segments (top 60% by RMS), but at least 2
    if len(segments) > 1:
        seg_rms = [float(torch.sqrt((seg**2).mean()).item()) for seg in segments]
        idx_sorted = sorted(range(len(segments)), key=lambda i: seg_rms[i], reverse=True)
        keep = max(2, int(round(0.6 * len(segments))))
        segments = [segments[i] for i in idx_sorted[:keep]]

    seg_cosines = []
    seg_embeds = []
    with torch.no_grad():
        for seg in segments:
            if seg.shape[-1] < int(0.6 * SAMPLE_RATE):
                continue
            emb = model.encode_batch(seg)
            if emb.ndim == 3:
                emb = emb.squeeze(0)
            if emb.ndim == 2:
                emb = emb.mean(dim=0)
            emb = emb / (emb.norm(p=2) + 1e-8)
            seg_embeds.append(emb)
            c = torch.nn.functional.cosine_similarity(
                emb.unsqueeze(0), stored_embedding.unsqueeze(0), dim=1
            ).item()
            seg_cosines.append(float(c))

    if not seg_cosines:
        messagebox.showerror("Verification Error", "Recording too short/noisy. Please try again.")
        root.destroy()
        return False

    seg_cosines_np = np.array(seg_cosines, dtype=np.float32)
    K = max(2, int(round(0.5 * len(seg_cosines_np))))  # top 50%, at least 2
    topk = np.sort(seg_cosines_np)[-K:]
    seg_score = float(np.median(topk))

    print(f"[DEBUG] full_cos={full_cos:.3f}")
    print(f"[DEBUG] seg_cos={np.round(seg_cosines_np,3)} | topK={K}, seg_score={seg_score:.3f}")

    # ---------- Score fusion ----------
    alpha = 0.7  # weight for full-utterance score
    raw_score = alpha * full_cos + (1.0 - alpha) * seg_score

    # --- Build an aggregate probe embedding ONLY for z-norm (optional if you have cohort) ---
    agg_probe = torch.stack(seg_embeds, dim=0).mean(dim=0) if len(seg_embeds) > 0 else full_emb
    agg_probe = agg_probe / (agg_probe.norm(p=2) + 1e-8)

    # --- Z-Norm using cohort (if available) ---
    cohort = load_cohort(VOICEPRINTS_DIR, username)

    if len(cohort) >= 5:
        with torch.no_grad():
            coh_scores = [
                torch.nn.functional.cosine_similarity(
                    agg_probe.unsqueeze(0), c.unsqueeze(0), dim=1
                ).item()
                for c in cohort
            ]
        cs = np.array(coh_scores, dtype=np.float32)
        m = float(np.median(cs))
        mad = float(np.median(np.abs(cs - m)))
        sigma = 1.4826 * mad + 1e-6  # MAD->std
        score = (raw_score - m) / sigma
        threshold = 0.0
        print(f"raw={raw_score:.3f} | z={score:.3f} (med={m:.3f}, mad={mad:.3f}) | thr={threshold:.3f}")
    else:
        score = raw_score
        threshold = VERIFICATION_THRESHOLD
        print(f"raw(full)={full_cos:.3f}  raw(seg)={seg_score:.3f}  fused={raw_score:.3f} | thr={threshold:.3f} (no cohort)")

    # --- Final decision & UI feedback ---
    success = score >= threshold
    print(f"raw(full)={full_cos:.3f}  raw(seg)={seg_score:.3f}  fused={raw_score:.3f} | thr={threshold:.3f} (no cohort) -> RESULT: {'PASS' if success else 'FAIL'}")
    messagebox.showinfo(
        "Verification Result",
        f"Full: {full_cos:.3f} | Seg: {seg_score:.3f} | Fused: {raw_score:.3f} | Thr: {threshold:.3f}"
    )

    root.destroy()
    return success


def self_check() -> bool:
    """
    Record two back-to-back 5s samples with the same phrase and report
    how similar they are using the same pipeline you use in verify():
      - peak normalize
      - trim (0.005)
      - full-utterance embedding
      - segmented top-K median stabilization
      - 0.7/0.3 score fusion
    Prints PASS/FAIL vs VERIFICATION_THRESHOLD and shows a dialog.
    """
    try:
        phrase = "My voice is my password; please grant access to my account."
        # --- Record #1 ---
        prompt1 = f"Self-check step 1/2:\nPlease say '{phrase}' clearly for {DURATION} seconds."
        messagebox.showinfo("Self-check • First Recording", prompt1)
        rec1 = record_audio(duration=DURATION, prompt=prompt1, gui_mode=True)
        if rec1 is None:
            messagebox.showwarning("Self-check Cancelled", "First recording cancelled.")
            return False
        rec1 = rec1 / (float(np.max(np.abs(rec1))) + 1e-6)
        if float(np.sqrt(np.mean(rec1**2))) < 0.01:
            messagebox.showwarning("Low Volume", "First recording seems silent.")
            return False

        # --- Record #2 ---
        prompt2 = f"Self-check step 2/2:\nPlease repeat:\n'{phrase}' for {DURATION} seconds."
        messagebox.showinfo("Self-check • Second Recording", prompt2)
        rec2 = record_audio(duration=DURATION, prompt=prompt2, gui_mode=True)
        if rec2 is None:
            messagebox.showwarning("Self-check Cancelled", "Second recording cancelled.")
            return False
        rec2 = rec2 / (float(np.max(np.abs(rec2))) + 1e-6)
        if float(np.sqrt(np.mean(rec2**2))) < 0.01:
            messagebox.showwarning("Low Volume", "Second recording seems silent.")
            return False

        # --- Save to two different files (avoid overwrite) ---
        tmp1 = save_temp_audio(rec1, filename="selfcheck_1.wav")
        tmp2 = save_temp_audio(rec2, filename="selfcheck_2.wav")

        # --- Load model once ---
        with suppress_stdout():
            model = get_model()

        # helper to encode one wav with your same pipeline
        def encode_from_wav(path):
            sig, fs = torchaudio.load(path)
            sig = trim_silence(sig, threshold=0.005)
            if fs != SAMPLE_RATE:
                import torchaudio.functional as AF
                sig = AF.resample(sig, fs, SAMPLE_RATE)

            # full emb
            with torch.no_grad():
                full = model.encode_batch(sig)
            if full.ndim == 3:  # [1, T, D]
                full = full.squeeze(0)
            if full.ndim == 2:  # [T, D]
                full = full.mean(dim=0)
            full = full / (full.norm(p=2) + 1e-8)

            # segments (same params as verify)
            segs = sliding_windows(sig, SAMPLE_RATE, win_sec=1.5, hop_sec=0.5)
            segs = segs[:8]
            if len(segs) > 1:
                seg_rms = [float(torch.sqrt((s**2).mean()).item()) for s in segs]
                idx_sorted = sorted(range(len(segs)), key=lambda i: seg_rms[i], reverse=True)
                keep = max(2, int(round(0.6 * len(segs))))
                segs = [segs[i] for i in idx_sorted[:keep]]

            seg_embs = []
            with torch.no_grad():
                for s in segs:
                    if s.shape[-1] < int(0.6 * SAMPLE_RATE):
                        continue
                    e = model.encode_batch(s)
                    if e.ndim == 3:
                        e = e.squeeze(0)
                    if e.ndim == 2:
                        e = e.mean(dim=0)
                    e = e / (e.norm(p=2) + 1e-8)
                    seg_embs.append(e)

            if len(seg_embs) == 0:
                agg = full
            else:
                agg = torch.stack(seg_embs, dim=0).mean(dim=0)
                agg = agg / (agg.norm(p=2) + 1e-8)
            return full, agg

        full1, agg1 = encode_from_wav(tmp1)
        full2, agg2 = encode_from_wav(tmp2)

        # --- Compare ---
        full_cos = torch.nn.functional.cosine_similarity(
            full1.unsqueeze(0), full2.unsqueeze(0), dim=1
        ).item()
        seg_cos = torch.nn.functional.cosine_similarity(
            agg1.unsqueeze(0), agg2.unsqueeze(0), dim=1
        ).item()

        alpha = 0.7
        fused = alpha * full_cos + (1.0 - alpha) * seg_cos

        print(f"[SELF-CHECK] full={full_cos:.3f}  seg={seg_cos:.3f}  fused={fused:.3f} | thr={VERIFICATION_THRESHOLD:.3f}")
        passed = fused >= VERIFICATION_THRESHOLD
        print(f"[SELF-CHECK] RESULT: {'PASS' if passed else 'FAIL'}")

        messagebox.showinfo(
            "Self-check Result",
            f"Full: {full_cos:.3f} | Seg: {seg_cos:.3f} | Fused: {fused:.3f}\n"
            f"Threshold: {VERIFICATION_THRESHOLD:.3f}\n\n"
            f"Result: {'PASS ✅' if passed else 'FAIL ❌'}"
        )
        return passed

    except Exception as e:
        print("[SELF-CHECK] ERROR:", repr(e))
        messagebox.showerror("Self-check Error", f"{type(e).__name__}: {e}")
        return False
    finally:
        # cleanup temps
        for p in ("selfcheck_1.wav", "selfcheck_2.wav"):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
