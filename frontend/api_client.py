import requests
import json

class APIClient:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url

    def _handle_response(self, response):
        try: return response.json()
        except json.JSONDecodeError: return {"status": "error", "message": "Invalid server response."}

    def check_server_status(self):
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=3)
            return response.status_code == 200
        except: return False

    def register_user(self, user_data):
        try:
            response = requests.post(f"{self.base_url}/api/register", json=user_data)
            return self._handle_response(response)
        except Exception as e: return {"status": "error", "message": f"Connection error: {e}"}

    def enroll_voice(self, username, audio_filepath):
        try:
            with open(audio_filepath, 'rb') as f:
                files = {'audio_file': f}
                data = {'username': username}
                response = requests.post(f"{self.base_url}/api/enroll_voice", files=files, data=data, timeout=30)
            return self._handle_response(response)
        except Exception as e: return {"status": "error", "message": f"Connection error: {e}"}

    def check_enrollment(self, username):
        try:
            response = requests.post(f"{self.base_url}/api/check_enrollment", json={"username": username})
            return self._handle_response(response)
        except Exception as e: return {"enrolled": False, "message": f"Connection error: {e}"}

    def verify_voice(self, username, audio_filepath):
        try:
            with open(audio_filepath, 'rb') as f:
                files = {'audio_file': f}
                data = {'username': username}
                response = requests.post(f"{self.base_url}/api/verify_voice", files=files, data=data, timeout=30)
            return self._handle_response(response)
        except Exception as e: return {"verified": False, "message": f"Connection error: {e}"}

    def login(self, username, password):
        try:
            response = requests.post(f"{self.base_url}/api/login", json={"username": username, "password": password})
            return self._handle_response(response)
        except Exception as e: return {"login_success": False, "message": f"Connection error: {e}"}