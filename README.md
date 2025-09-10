# keyvox

# gawa muna kayo own branch nio guys ha

# then pag na merge nio na, delete nio na branch nio

# tas fetch origin ulet then create branch ulet para malinis

Changes to the frontend/backend Actions
1. Get Username 
Frontend (app.py): User types their username into a Tkinter dialog box.

2. . Record Audio
- Frontend (app.py): The user clicks the mic icon. The _record_audio_blocking function uses pyaudio to record a .wav file and saves it to a temporary folder.
- The responsibility for recording moved to the frontend (which is correct), but the core action of capturing audio from the microphone is identical.

3. Send Audio
- Frontend (api_client.py): The frontend sends the temporary .wav file to the backend server via an HTTP POST request.
- This is the "wiring." Instead of the logic being in the same file, the audio data is now sent over a local network connection to the server. The data itself is unchanged.

4. Perform Quality Checks
- Backend (helpers.py): The perform_quality_checks function runs the exact same RMS (volume) and duration checks as your original enroll.py script.
- The code for this is a direct copy-paste of your original logic, just organized into a reusable function.

5. Load the Model
- Backend (helpers.py): The get_model() function loads the exact same SpeechBrain model from the same source. This is done once when the server.py starts.
- This is identical to your original helpers.py.

6. Create Voiceprint (Enrollment)
- Backend (server.py): The /api/enroll endpoint takes the good-quality audio, runs app.model.encode_batch(signal), and saves the resulting tensor to a .pt file, just like your enroll.py did.
- The core PyTorch and SpeechBrain calls are identical.

7. Compare Voices (Verification)
- Backend (server.py): The /api/verify endpoint loads the user's saved .pt file, creates a new embedding from the live audio, and runs app.model.similarity(). It then compares the score to VERIFICATION_THRESHOLD.
-  This is a direct translation of the logic from your verify.py main function.

What is "New"?
The only new logic is the database.py file. Your prototype had no concept of user accounts, passwords, or emails.
It only knew about voiceprint files.


1. Your Text Data (Name, Email, Password)
This is all the information you type into the "STEP 1: Account Setup" form.
    File Name: keyvox.db
    Location: backend/data/keyvox.db

The Journey:
1. You fill out the form in the Tkinter frontend.
2. When you click "Next Step," the frontend's api_client.py sends this text data to the backend's /api/register endpoint.
3. The backend server (server.py) receives the data.
4. It calls the database.py script, which hashes your password for security (it never stores the plain password).
5. It then inserts your full_name, username, email, and the password_hash as a new row in the users table inside the keyvox.db database file.

keyvox.db is a SQLite database file. 

2. Your Voice Data (The Voiceprint)
This is the audio you record in the "STEP 2: Voice Enrollment" screen.
    File Name: your_username.pt (e.g., julss.pt)
    Location: backend/data/voiceprints/your_username.pt

The Journey:
1. You record your voice in the Tkinter frontend. This creates a temporary file like frontend/temp_audio/enroll_julss.wav.
2. The frontend's api_client.py uploads this .wav file to the backend's /api/enroll endpoint.
3. The backend server saves this .wav file temporarily.
4. It runs the core logic from your original enroll.py: it performs quality checks and then uses 
   the SpeechBrain model to process the audio into a mathematical representation called a voiceprint (a PyTorch tensor).
5. The server saves this voiceprint as a new .pt file inside the backend/data/voiceprints/ folder.
6. Crucially, the server then updates your row in the keyvox.db database, adding the path backend/data/voiceprints/julss.pt to your record. 
   This links your user account to your unique voiceprint file.

   