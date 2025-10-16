# utils/validators.py
import re
from tkinter import messagebox

def validate_email(email: str) -> tuple[bool, str]:
    """
    Validates an email address.
    Returns (is_valid, error_message).
    """
    if not email:
        messagebox.showerror("Error", "Email cannot be empty.")
        return False, "Email cannot be empty."
    # Simple regex for email validation
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, email):
        messagebox.showerror("Error", "Please enter a valid email address.")
        return False, "Please enter a valid email address."
    return True, ""

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validates a password.
    Returns (is_valid, error_message).
    """
    if len(password) < 8:
        messagebox.showerror("Error", "Password must be at least 8 characters.\nInclude uppercase, lowercase, number, and special character.")    
        return False, "Password must be at least 8 characters. \nInclude uppercase, lowercase, number, and special character."
    if not any(c.isupper() for c in password):
        messagebox.showerror("Error", "Password must be at least 8 characters.\nInclude uppercase, lowercase, number, and special character.") 
        return False, "Password must contain an uppercase letter."
    if not any(c.islower() for c in password):
        messagebox.showerror("Error", "Password must be at least 8 characters.\nInclude uppercase, lowercase, number, and special character.")
        return False, "Password must contain a lowercase letter."
    if not any(c.isdigit() for c in password):
        messagebox.showerror("Error", "Password must be at least 8 characters.\nInclude uppercase, lowercase, number, and special character.")
        return False, "Password must contain a number."
    if not any(c in "!@#$%^&*()_+-=[]{};'😕.<>?/|\\`~" for c in password):
        messagebox.showerror("Error", "Password must be at least 8 characters.\nInclude uppercase, lowercase, number, and special character(!, @, #, $, .....).") 
        return False, "Password must contain at least one special character." 
    return True, ""
