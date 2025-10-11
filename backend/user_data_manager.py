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
