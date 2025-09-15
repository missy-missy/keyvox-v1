import sqlite3
import hashlib
import os
from config import DATABASE_PATH, DATA_DIR

def init_db():
    """
    Initializes the database and creates the 'users' table if it doesn't exist.
    This function is essential and is called by the server on startup.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create the users table with all necessary columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            voiceprint_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def hash_password(password):
    """Hashes a password using SHA-256 for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(user_data):
    """
    Adds a new user to the database. Hashes the password before storing.
    :param user_data (dict): Contains 'username', 'full_name', 'email', 'password'.
    :return: True if successful, False otherwise.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, full_name, email, password_hash) VALUES (?, ?, ?, ?)",
            (
                user_data['username'].lower(),
                user_data['full_name'],
                user_data['email'],
                hash_password(user_data['password'])
            )
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # This error occurs if the username or email is already taken.
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    """

    Retrieves a user's data from the database by their username.
    :param username (str): The username to look up.
    :return: A dictionary with user data or None if not found.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    # Return rows as dictionary-like objects
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username.lower(),))
    user = cursor.fetchone()
    
    conn.close()
    return dict(user) if user else None

def update_voiceprint_path(username, path):
    """
    Updates a user's record with the path to their saved voiceprint file.
    :param username (str): The user to update.
    :param path (str): The file path of the voiceprint.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET voiceprint_path = ? WHERE username = ?",
        (path, username.lower())
    )
    
    conn.commit()
    conn.close()