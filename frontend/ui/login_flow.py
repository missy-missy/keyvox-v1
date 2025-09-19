import tkinter as tk
from tkinter import messagebox
import os
import frontend_config as config
from . import ui_helpers

def show_username_entry_screen(app):
    """Shows the screen for the user to enter their username."""
    app.login_flow_state = 'username_entry'
    card = ui_helpers.create_main_card(app, width=500, height=350)
    
    content_wrapper = tk.Frame(card, bg=config.CARD_BG_COLOR)
    content_wrapper.pack(expand=True)
    
    tk.Label(content_wrapper, text="Enter Username", font=app.font_large, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=(20, 10))
    
    app.username_error_label = tk.Label(content_wrapper, text="", font=app.font_small, fg=config.ERROR_COLOR, bg=config.CARD_BG_COLOR)
    app.username_error_label.pack(pady=(0, 10))
    
    app.username_entry = tk.Entry(content_wrapper, font=app.font_large, fg=config.TEXT_COLOR, bg=config.GRADIENT_TOP_COLOR, width=25, relief="solid", borderwidth=1, justify="center")
    app.username_entry.pack(pady=10, ipady=5)
    app.username_entry.focus_set()
    
    tk.Button(content_wrapper, text="Continue", font=app.font_normal, bg=config.BUTTON_COLOR, fg=config.TEXT_COLOR, relief="flat", padx=20, pady=5, command=app._handle_username_submit).pack(pady=(20, 15))

def handle_username_submit(app):
    """Validates the entered username with the backend."""
    username = app.username_entry.get()
    if not username:
        app.username_error_label.config(text="Username cannot be empty.")
        return

    enrollment_status = app.api.check_enrollment(username)

    if enrollment_status.get("enrolled"):
        app.login_attempt_user = {"username": username.lower()}
        show_login_voice_auth_screen(app)
    else:
        message = enrollment_status.get("message", "An unknown error occurred.")
        app.username_error_label.config(text=message)
        app.username_entry.delete(0, 'end')

def show_login_voice_auth_screen(app):
    """Shows the voice recording UI for login verification."""
    app.login_flow_state = 'voice_auth'
    card = ui_helpers.create_main_card(app, width=600, height=350)
    username = app.login_attempt_user.get("username", "user")
    
    tk.Label(card, text=f'Welcome, {username}!', font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=(30, 10))
    tk.Label(card, text=f'Please say "My voice is my password"', font=app.font_large, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR, wraplength=500).pack(expand=True)
    
    mic_label = tk.Label(card, image=app.mic_img, bg=config.CARD_BG_COLOR, cursor="hand2")
    mic_label.pack(expand=True)
    mic_label.bind("<Button-1>", app._handle_login_voice_record)
    
    app.recording_status_label = tk.Label(card, text="Click the mic to authenticate", font=app.font_small, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR)
    app.recording_status_label.pack(pady=(0, 20))

def handle_login_voice_record(app, event=None):
    """Handles the recording and API verification for voice login."""
    username = app.login_attempt_user.get('username')
    if not username:
        messagebox.showerror("Error", "Username missing.")
        return

    app.recording_status_label.config(text="Recording (4s)...")
    app.root.update_idletasks()
    
    filepath = os.path.join(config.AUDIO_DIR, f"verify_{username}.wav")
    app._record_audio_blocking(filepath, duration=4)
    
    app.recording_status_label.config(text="Verifying...")
    app.root.update_idletasks()
    response = app.api.verify_voice(username, filepath)
    
    print(f"DEBUG: API response for user '{username}': {response}")
    
    if response.get("verified"):
        messagebox.showinfo("Success", "Voice Authenticated! Please enter your password.")
        show_password_screen(app)
    else:
        messagebox.showerror("Failure", f"Voice authentication failed.\n{response.get('message', 'Please try again.')}")
        app.show_home_screen()

def show_password_screen(app):
    """Shows the final password entry screen."""
    app.login_flow_state = 'password_entry'
    card = ui_helpers.create_main_card(app, width=500, height=350)
    
    content_wrapper = tk.Frame(card, bg=config.CARD_BG_COLOR)
    content_wrapper.pack(expand=True)
    
    tk.Label(content_wrapper, text="Enter Password", font=app.font_large, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=(20, 10))
    app.error_label = tk.Label(content_wrapper, text="", font=app.font_small, fg=config.ERROR_COLOR, bg=config.CARD_BG_COLOR)
    app.error_label.pack(pady=(0, 10))
    
    app.password_entry = tk.Entry(content_wrapper, font=app.font_large, fg=config.TEXT_COLOR, bg=config.GRADIENT_TOP_COLOR, show="*", width=25, relief="solid", borderwidth=1, justify="center")
    app.password_entry.pack(pady=10, ipady=5)
    app.password_entry.focus_set()
    
    tk.Button(content_wrapper, text="Confirm Login", font=app.font_normal, bg=config.BUTTON_COLOR, fg=config.TEXT_COLOR, relief="flat", padx=20, pady=5, command=app._check_password).pack(pady=(20, 15))

def check_password(app):
    """Validates the password with the backend to complete the login."""
    password = app.password_entry.get()
    
    if not app.login_attempt_user:
        app.error_label.config(text="Login session expired. Please start over.")
        app.root.after(2000, app.show_home_screen)
        return
    
    username = app.login_attempt_user.get('username')
    if not username or not password:
        app.error_label.config(text="An error occurred.")
        return

    response = app.api.login(username, password)
    if response.get("login_success"):
        app.currently_logged_in_user = response.get("user_details")
        app.login_attempt_user = None
        app.show_home_screen()
    else:
        app.error_label.config(text=response.get("message", "Incorrect Password."))
        app.password_entry.delete(0, 'end')