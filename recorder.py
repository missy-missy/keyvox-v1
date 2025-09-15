import pygame
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import os
from datetime import datetime
import threading
import math

# --- Configuration ---
# GUI Settings
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
GRAY = (50, 50, 50)
BLUE = (0, 150, 255)

# Audio Settings
SAMPLE_RATE = 44100
CHANNELS = 1
FOLDER_NAME = "recordings"

# --- Global State Variables ---
is_recording = False
audio_frames = []
recording_thread = None

# --- Helper Functions ---

def save_recording():
    """Saves the recorded audio frames to a WAV file."""
    global audio_frames
    if not audio_frames:
        print("No audio recorded to save.")
        return

    print("Saving recording...")
    recording = np.concatenate(audio_frames, axis=0)
    audio_frames = [] # Clear frames for the next recording

    # Get the script's directory and create the recordings folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    recordings_dir = os.path.join(script_dir, FOLDER_NAME)
    os.makedirs(recordings_dir, exist_ok=True)
    
    # Generate filename and save
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"recording_{timestamp}.wav"
    filepath = os.path.join(recordings_dir, filename)
    
    try:
        write(filepath, SAMPLE_RATE, recording)
        print(f"✅ Recording saved successfully to: {filepath}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

def record_audio_thread():
    """The function that runs in a separate thread to record audio."""
    global is_recording, audio_frames

    def callback(indata, frames, time, status):
        """This is called for each audio block from the microphone."""
        if status:
            print(status)
        audio_frames.append(indata.copy())

    # Use an InputStream which runs until it's explicitly stopped
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
        while is_recording:
            sd.sleep(100) # Wait in the thread without busy-looping
    
    # After the loop finishes, save the file
    save_recording()


# --- Main Application ---
def main():
    """Main function to run the Pygame application."""
    global is_recording, recording_thread, audio_frames

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Voice Recorder")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("sans-serif", 30)

    # Button properties
    button_center = (WIDTH // 2, HEIGHT // 2)
    button_radius = 80
    
    # Animation properties
    animation_counter = 0

    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if is_recording:
                    is_recording = False # Signal thread to stop
                    recording_thread.join() # Wait for it to finish
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if the click is inside the button circle
                mouse_pos = pygame.mouse.get_pos()
                distance = math.sqrt((mouse_pos[0] - button_center[0])**2 + (mouse_pos[1] - button_center[1])**2)
                
                if distance < button_radius:
                    if not is_recording:
                        # --- Start Recording ---
                        is_recording = True
                        audio_frames = [] # Reset frames
                        # Start the recording in a new thread to not freeze the GUI
                        recording_thread = threading.Thread(target=record_audio_thread)
                        recording_thread.start()
                        print("🎤 Recording started...")
                    else:
                        # --- Stop Recording ---
                        is_recording = False
                        # The thread will auto-stop and save the file
                        print("🎤 Recording stopping...")

        # --- Drawing Logic ---
        screen.fill(GRAY)

        # Draw the pulsating "wave" if recording
        if is_recording:
            animation_counter += 1
            # Create a smooth sine wave pulse
            pulse_alpha = (math.sin(animation_counter * 0.1) + 1) / 2 # Normalize to 0-1
            pulse_radius = button_radius + 20 + (pulse_alpha * 20)
            
            # Create a transparent surface for the pulse
            pulse_surface = pygame.Surface((pulse_radius * 2, pulse_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(pulse_surface, (*BLUE, 70), (pulse_radius, pulse_radius), pulse_radius)
            screen.blit(pulse_surface, (button_center[0] - pulse_radius, button_center[1] - pulse_radius))

        # Draw the main button circle
        pygame.draw.circle(screen, RED if not is_recording else BLUE, button_center, button_radius)
        
        # Draw text instructions
        if not is_recording:
            text = font.render("Click to Record", True, WHITE)
        else:
            text = font.render("Recording...", True, WHITE)
            
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - button_radius - 30))
        screen.blit(text, text_rect)

        # Update the display
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()