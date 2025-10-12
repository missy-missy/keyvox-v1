from pathlib import Path
import json

# users.json in the same folder as this script
USER_FILE = Path(__file__).parent / "users.json"

def update_email(old_email, new_email, user_file=USER_FILE):
    """
    Updates a user's email from old_email to new_email in users.json.
    """
    with open(user_file, "r") as f:
        users = json.load(f)

    for user in users.values():
        if user.get("email") == old_email:
            user["email"] = new_email
            with open(user_file, "w") as f:
                json.dump(users, f, indent=4)
            return

    raise ValueError(f"No user with email '{old_email}' found.")

def load_users(user_file=USER_FILE):
    """Load all users from users.json"""
    with open(user_file, "r") as f:
        return json.load(f)

def get_user_by_username(username, user_file=USER_FILE):
    """Find user data by username"""
    users = load_users(user_file)
    for user in users.values():
        if user.get("username", "").lower() == username.lower():
            return user
    return None

def get_user_by_email(email, user_file=USER_FILE):
    """Find user data by email"""
    users = load_users(user_file)
    for user in users.values():
        if user.get("email", "").lower() == email.lower():
            return user
    return None

def update_email_by_name_and_blank_email(full_name, new_email, user_file=USER_FILE):
    """
    Updates a user's email using their full name, only if their email is blank.
    """
    with open(user_file, "r") as f:
        users = json.load(f)

    for user in users.values():
        if user.get("full_name") == full_name and user.get("email") == "":
            user["email"] = new_email
            with open(user_file, "w") as f:
                json.dump(users, f, indent=4)
            return

    raise ValueError(f"No user with full_name '{full_name}' and blank email found.")
