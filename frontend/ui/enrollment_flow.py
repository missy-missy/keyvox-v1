import tkinter as tk
from tkinter import messagebox
import os
import frontend_config as config
from . import ui_helpers

def navigate_to_enrollment(app, event=None):
    """Entry point for the enrollment flow."""
    show_enrollment_step1(app)

def show_enrollment_step1(app):
    """Shows the account setup form (name, username, password)."""
    app.enrollment_state = 'step1_account_setup'
    app.new_enrollment_data = {}
    card = ui_helpers.create_main_card(app, width=700, height=450)
    ui_helpers.update_nav_selection(app, "enrollment")
    
    tk.Label(card, text="STEP 1: Account Setup", font=app.font_large_bold, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).grid(row=0, column=0, columnspan=2, sticky="w", pady=(20, 5), padx=40)
    tk.Label(card, text="Enter your basic account information", font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 25), padx=40)
    
    fields = {"Full Name:": "full_name", "Username:": "username", "Email:": "email", "Password:": "password", "Confirm Password:": "confirm_password"}
    app.entry_widgets = {}
    for i, (label, key) in enumerate(fields.items()):
        tk.Label(card, text=label, font=app.font_large, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).grid(row=i + 2, column=0, sticky="w", pady=8, padx=(40, 20))
        entry = tk.Entry(card, font=app.font_large, width=25, bg=config.GRADIENT_TOP_COLOR, fg=config.TEXT_COLOR, relief="solid", bd=1)
        app.entry_widgets[key] = entry
        if "Password" in label:
            entry.config(show="*")
        entry.grid(row=i + 2, column=1, pady=8, ipady=4, padx=(0, 40))
        
    app.enroll_error_label = tk.Label(card, text="", font=app.font_small, fg=config.ERROR_COLOR, bg=config.CARD_BG_COLOR)
    app.enroll_error_label.grid(row=len(fields) + 2, column=0, columnspan=2, pady=(10, 0))
    
    bf = tk.Frame(app.content_frame, bg="#7c2e50")
    bf.pack(fill="x", padx=60, pady=(0, 10))
    tk.Label(bf, text="● ○ ○", font=app.font_large, fg=config.TEXT_COLOR, bg="#7c2e50").pack(side="left")
    tk.Button(bf, text="Next Step →", font=app.font_normal, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=15, pady=5, command=app._validate_step1).pack(side="right")

def validate_step1(app):
    """Validates the user registration form and sends data to the API."""
    data = {key: entry.get() for key, entry in app.entry_widgets.items()}
    if not all(v for k, v in data.items() if k != 'confirm_password'):
        app.enroll_error_label.config(text="All fields are required.")
        return
    if data["password"] != data["confirm_password"]:
        app.enroll_error_label.config(text="Passwords do not match.")
        return
        
    reg_data = {k: v for k, v in data.items() if k != 'confirm_password'}
    response = app.api.register_user(reg_data)
    
    if response.get("status") == "success":
        app.new_enrollment_data = reg_data
        app.enroll_error_label.config(text="")
        show_enrollment_step2(app)
    else:
        app.enroll_error_label.config(text=response.get("message", "Registration failed."))

def show_enrollment_step2(app):
    """Shows the introduction screen for the voice enrollment part."""
    app.enrollment_state = 'step2_voice_intro'
    card = ui_helpers.create_main_card(app, width=700, height=350)
    
    tk.Label(card, text="STEP 2: Voice Authentication", font=app.font_large_bold, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(anchor="w", pady=(20, 5), padx=40)
    tk.Label(card, text="Record your voice for added security. You will record 5 phrases.\nThis allows the system to recognize your unique voiceprint.", font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR, justify="left").pack(anchor="w", pady=(0, 25), padx=40)
    
    bf = tk.Frame(app.content_frame, bg="#7c2e50")
    bf.pack(fill="x", padx=60, pady=(0, 10))
    tk.Button(bf, text="< Back", font=app.font_normal, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=15, pady=5, command=lambda: show_enrollment_step1(app)).pack(side="left")
    tk.Label(bf, text="○ ● ○", font=app.font_large, fg=config.TEXT_COLOR, bg="#7c2e50").pack(side="left", padx=20)
    tk.Button(bf, text="Start →", font=app.font_normal, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=15, pady=5, command=lambda: show_enrollment_voice_record(app)).pack(side="right")

def show_enrollment_voice_record(app):
    """The main screen for recording the enrollment phrases."""
    app.enrollment_state = 'step3_voice_record'
    card = ui_helpers.create_main_card(app, width=600, height=350)
    
    tk.Label(card, text=f"{app.current_phrase_index + 1} of {len(app.enrollment_phrases)}:", font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=(20, 0))
    tk.Label(card, text=f'"{app.enrollment_phrases[app.current_phrase_index]}"', font=app.font_large_bold, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR, wraplength=500).pack(expand=True)
    
    mic_label = tk.Label(card, image=app.mic_img, bg=config.CARD_BG_COLOR, highlightthickness=0, cursor="hand2")
    mic_label.pack(pady=10)
    mic_label.bind("<Button-1>", app.toggle_recording)
    
    app.recording_status_label = tk.Label(card, text="Click the mic to record", font=app.font_small, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR)
    app.recording_status_label.pack(pady=(0, 20))
    
    bf = tk.Frame(app.content_frame, bg="#7c2e50")
    bf.pack(fill="x", padx=60, pady=(0, 10))
    tk.Button(bf, text="< Back", font=app.font_normal, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=15, pady=5, command=app._go_back_phrase).pack(side="left")
    app.next_btn = tk.Button(bf, text="Next →", font=app.font_normal, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=15, pady=5, command=app._go_next_phrase, state="disabled")
    app.next_btn.pack(side="right")

def go_back_phrase(app):
    """Navigates to the previous phrase or step in enrollment."""
    if app.current_phrase_index > 0:
        app.current_phrase_index -= 1
        show_enrollment_voice_record(app)
    else:
        show_enrollment_step2(app)

def go_next_phrase(app):
    """Navigates to the next phrase or finishes the enrollment."""
    if app.current_phrase_index < len(app.enrollment_phrases) - 1:
        app.current_phrase_index += 1
        show_enrollment_voice_record(app)
    else:
        handle_final_enrollment_upload(app)

def handle_final_enrollment_upload(app):
    """Uploads the primary voice recording to the backend."""
    username = app.new_enrollment_data.get("username")
    filepath = os.path.join(config.AUDIO_DIR, f"{username}_phrase_1.wav")
    if not os.path.exists(filepath):
        messagebox.showerror("Error", "Primary enrollment audio not found. Please record phrase 1 again.")
        return

    response = app.api.enroll_voice(username, filepath)
    if response.get("status") == "success":
        show_enrollment_summary(app)
    else:
        messagebox.showerror("Enrollment Failed", response.get("message", "Final enrollment failed."))

def show_enrollment_summary(app):
    """Displays a summary of the successfully enrolled user's details."""
    card = ui_helpers.create_main_card(app, width=700, height=450)
    
    tk.Label(card, text="Enrollment Process Complete", font=app.font_large_bold, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).grid(row=0, column=0, columnspan=2, sticky="w", pady=(20, 5), padx=40)
    tk.Label(card, text="You've successfully enrolled. Your credentials are now securely registered.", font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR, justify="left").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 25), padx=40)
    
    summary_data = {
        "Full Name:": app.new_enrollment_data.get('full_name'),
        "Username:": app.new_enrollment_data.get('username'),
        "Password:": '********',
        "Email:": app.new_enrollment_data.get('email'),
        "Voice Pattern:": "Saved"
    }
    for i, (label, value) in enumerate(summary_data.items()):
        tk.Label(card, text=label, font=app.font_large, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).grid(row=i + 2, column=0, sticky="w", pady=5, padx=40)
        tk.Label(card, text=value, font=app.font_large, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).grid(row=i + 2, column=1, sticky="w", pady=5, padx=20)
        
    tk.Button(card, text="Finish", font=app.font_normal, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=30, pady=5, command=app._finish_enrollment).grid(row=len(summary_data) + 2, column=0, columnspan=2, pady=30)

def finish_enrollment(app):
    """Finalizes enrollment and redirects to the home screen for login."""
    messagebox.showinfo("Success", "New user enrollment complete! Please log in.")
    app.just_enrolled_username = app.new_enrollment_data.get("username")
    app.just_enrolled = True
    app.enrollment_state = 'not_started'
    app.show_home_screen()