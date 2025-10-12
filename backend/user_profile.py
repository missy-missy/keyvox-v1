# user_profile.py

import json
from pathlib import Path

USER_DATA_FILE = Path("data/users.json")
SESSION_FILE = Path("data/session.json")


def load_all_users():
    if USER_DATA_FILE.exists():
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return []


def get_user_by_username(username):
    users = load_all_users()
    for user in users:
        if user["username"].lower() == username.lower():
            return user
    return None


def save_session(user):
    with open(SESSION_FILE, "w") as f:
        json.dump(user, f)


def load_session():
    if SESSION_FILE.exists():
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return None


def clear_session():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
