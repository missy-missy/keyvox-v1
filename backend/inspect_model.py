# inspect_model.py
import os
import tensorflow as tf

print("--- Inspecting Saved Model ---")

# --- Load the Model ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "lstm_voice_model.h5")
print(f"Loading model from: {MODEL_PATH}")
model = tf.keras.models.load_model(MODEL_PATH)

# --- Print the Model Summary ---
# This will show the name, type, and output shape of every layer.
print("\n--- Model Summary ---")
model.summary()

# --- Alternative: Loop and Print Layer Details ---
print("\n--- Detailed Layer Information ---")
for i, layer in enumerate(model.layers):
    print(f"Layer Index: {i}, Layer Name: {layer.name}, Output Shape: {layer.output_shape}")