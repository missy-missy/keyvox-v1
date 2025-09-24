import os
import tensorflow as tf
import numpy as np
import librosa

# --- Configuration (MUST MATCH YOUR TRAINING NOTEBOOK) ---
SAMPLE_RATE = 16000
N_MFCC = 13
MAX_LEN = 200 # You used 200 in your final training run

# --- Load the Model and Create the Embedding Extractor ---
# This section runs only ONCE when the server starts. It's highly efficient.
print("--- Loading custom trained LSTM model ---")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "lstm_voice_model.h5")

# 1. Load the full model that you trained
main_model = tf.keras.models.load_model(MODEL_PATH)

# 2. The "voiceprint" or "embedding" is the output of the second-to-last layer.
#    We create a new, specialized model that stops at this layer to extract the features.
embedding_model = tf.keras.Model(
    inputs=main_model.inputs,
    outputs=main_model.layers[4].output # This is the output of the Dense(64) layer
)
print("✅ Custom model and embedding extractor created successfully.")


def get_voice_embedding(audio_filepath):
    """
    Takes the path to an audio file, processes it exactly like the training data,
    and returns a 64-dimension numerical voiceprint (embedding).
    """
    try:
        # 1. Load and Standardize Audio
        audio, sr = librosa.load(audio_filepath, sr=SAMPLE_RATE, mono=True)
        
        # 2. Trim Silence (Voice Activity Detection)
        audio_trimmed, _ = librosa.effects.trim(audio, top_db=20)

        # 3. Extract MFCCs
        mfccs = librosa.feature.mfcc(y=audio_trimmed, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
        mfccs = mfccs.T # Transpose to (time, features)
        
        # 4. Pad or Truncate to the fixed length the model expects
        if mfccs.shape[0] > MAX_LEN:
            mfccs = mfccs[:MAX_LEN, :]
        else:
            padding = np.zeros((MAX_LEN - mfccs.shape[0], N_MFCC))
            mfccs = np.vstack((mfccs, padding))

        # 5. Add a "batch" dimension because the model expects it
        mfccs = np.expand_dims(mfccs, axis=0)

        # 6. Use our specialized embedding model to get the voiceprint
        embedding = embedding_model.predict(mfccs)
        
        # The output is a batch of 1, so we squeeze it to a simple 1D array
        return embedding.flatten()

    except Exception as e:
        print(f"Error processing audio file {audio_filepath}: {e}")
        return None


def preprocess_single_audio_file(audio_filepath):
    """
    Takes a single audio file path and processes it into a single,
    correctly shaped MFCC array for model input.
    """
    try:
        # This logic is the same as in get_voice_embedding
        audio, sr = librosa.load(audio_filepath, sr=SAMPLE_RATE, mono=True)
        audio_trimmed, _ = librosa.effects.trim(audio, top_db=20)
        mfccs = librosa.feature.mfcc(y=audio_trimmed, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
        mfccs = mfccs.T
        if mfccs.shape[0] > MAX_LEN:
            mfccs = mfccs[:MAX_LEN, :]
        else:
            padding = np.zeros((MAX_LEN - mfccs.shape[0], N_MFCC))
            mfccs = np.vstack((mfccs, padding))
        return mfccs
    except Exception as e:
        print(f"Error in preprocess_single_audio_file: {e}")
        return None