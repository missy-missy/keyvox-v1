import requests
import os

# The "phone number" for your backend server.
# This assumes your backend is running on the same machine on port 5000.
BACKEND_URL = "http://127.0.0.1:5000/api"

class APIClient:
    """
    A dedicated class for making all HTTP requests to the backend server.
    """
    def check_server_status(self):
        """Checks if the backend server is running and reachable."""
        try:
            # We add a timeout to prevent the app from hanging indefinitely.
            response = requests.get(f"{BACKEND_URL}/status", timeout=3)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            # This catches connection errors, timeouts, etc.
            return False

    def register_user(self, user_data):
        """
        Sends new user data (name, username, password, email) to the backend.
        :param user_data (dict): A dictionary containing user registration info.
        :return: The JSON response from the server as a dictionary.
        """
        try:
            response = requests.post(f"{BACKEND_URL}/register", json=user_data)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error during registration: {e}")
            return {"status": "error", "message": "Cannot connect to the server."}

    def login(self, username, password):
        """
        Sends login credentials to the backend for password verification.
        :param username (str): The user's username.
        :param password (str): The user's password.
        :return: The JSON response from the server.
        """
        try:
            payload = {"username": username, "password": password}
            response = requests.post(f"{BACKEND_URL}/login", json=payload)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error during login: {e}")
            return {"login_success": False, "message": "Cannot connect to the server."}

    def enroll_voice(self, username, audio_filepath):
        """
        Sends a user's audio file (.wav) to the backend for enrollment.
        This uses a multipart/form-data POST request to upload the file.
        :param username (str): The username to associate with the voiceprint.
        :param audio_filepath (str): The local path to the .wav file.
        :return: The JSON response from the server.
        """
        if not os.path.exists(audio_filepath):
            return {"status": "error", "message": "Audio file not found."}
        try:
            with open(audio_filepath, 'rb') as f:
                # 'files' is a special argument for file uploads in requests
                files = {'audio_file': (os.path.basename(audio_filepath), f, 'audio/wav')}
                data = {'username': username}
                response = requests.post(f"{BACKEND_URL}/enroll", files=files, data=data)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error during voice enrollment: {e}")
            return {"status": "error", "message": "Cannot connect to the server."}

    def check_enrollment(self, username):
        """
        Performs a pre-check to see if a user is enrolled for voice auth.
        :param username (str): The username to check.
        :return: The JSON response from the server.
        """
        try:
            payload = {"username": username}
            response = requests.post(f"{BACKEND_URL}/check_enrollment", json=payload)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error during enrollment check: {e}")
            return {"enrolled": False, "message": "Cannot connect to the server."}

    def verify_voice(self, username, audio_filepath):
        """
        Sends a user's live audio file for verification against their voiceprint.
        :param username (str): The user to verify.
        :param audio_filepath (str): The local path to the live .wav recording.
        :return: The JSON response from the server.
        """
        if not os.path.exists(audio_filepath):
            return {"verified": False, "message": "Audio file not found."}
        try:
            with open(audio_filepath, 'rb') as f:
                files = {'audio_file': (os.path.basename(audio_filepath), f, 'audio/wav')}
                data = {'username': username}
                response = requests.post(f"{BACKEND_URL}/verify", files=files, data=data)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error during voice verification: {e}")
            return {"verified": False, "message": "Cannot connect to the server."}