import tkinter as tk
from tkinter import messagebox
import os
import frontend_config as config
from . import ui_helpers

def navigate_to_enrollment(app, event=None):
    """Entry point for the enrollment flow."""
    # [FIX] This line updates the navbar to highlight "Enrollment"
    ui_helpers.update_nav_selection(app, "enrollment")
    show_enrollment_step1(app)
    
def show_enrollment_step1(app):
    """Shows the account setup form (name, username, password)."""
    LIGHT_CARD_BG = "#7C2E50"

    # --- FIX: clear content_frame before drawing enrollment ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.enrollment_state = 'step1_account_setup'
    app.new_enrollment_data = {}

    import tkinter.font as tkFont
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_label = tkFont.Font(family="Poppins", size=11)
    font_entry = tkFont.Font(family="Poppins", size=11)
    font_small = tkFont.Font(family="Poppins", size=9)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=700, height=400, bg=LIGHT_CARD_BG)
    card.pack(pady=30)
    card.pack_propagate(False)

    # --- [FIX #1] Tell the second column (index 1) to take up extra space ---
    card.grid_columnconfigure(1, weight=1)

    tk.Label(card, text="STEP 1: Account Setup", font=font_title,
             fg="white", bg=LIGHT_CARD_BG).grid(row=0, column=0, columnspan=2,
                                               sticky="w", pady=(20, 5), padx=40)
    tk.Label(card, text="Enter your basic account information",
             font=font_subtitle, fg="white", bg=LIGHT_CARD_BG).grid(row=1, column=0,
                                                                   columnspan=2,
                                                                   sticky="w",
                                                                   pady=(0, 20),
                                                                   padx=40)

    fields = {
        "Full Name:": "full_name",
        "Username:": "username",
        "Email:": "email",
        "Password:": "password",
        "Confirm Password:": "confirm_password"
    }

    app.entry_widgets = {}

    def make_password_field(parent, key):
        # This helper function is great, no changes needed here.
        entry_frame = tk.Frame(parent, bg="white")
        entry = tk.Entry(entry_frame, font=font_entry, width=22,
                         bg="white", fg="black", relief="flat", bd=0,
                         show="*", insertbackground="black")
        entry.pack(side="left", ipady=4, padx=(5, 0))
        app.entry_widgets[key] = entry

        def toggle_visibility():
            if entry.cget("show") == "*":
                entry.config(show="")
                btn.config(image=app.eye_closed_img)
            else:
                entry.config(show="*")
                btn.config(image=app.eye_open_img)

        btn = tk.Button(
            entry_frame,
            image=app.eye_open_img,
            bg="white", relief="flat", bd=0,
            activebackground="white",
            cursor="hand2",
            command=toggle_visibility
        )
        btn.pack(side="right", padx=(0, 5))
        return entry_frame

    for i, (label, key) in enumerate(fields.items()):
        tk.Label(card, text=label, font=font_label,
                 fg="white", bg=LIGHT_CARD_BG).grid(row=i + 2, column=0,
                                                    sticky="w", pady=6,
                                                    padx=(40, 20))

        if "Password" in label:
            frame = make_password_field(card, key)
            # --- [FIX #2] Use sticky="ew" to make the frame stretch horizontally ---
            frame.grid(row=i + 2, column=1, pady=6, padx=(0, 40), sticky="ew")
        else:
            entry = tk.Entry(card, font=font_entry, width=25,
                             bg="white", fg="black", relief="flat", bd=0,
                             insertbackground="black")
            # --- [FIX #3] Use sticky="ew" to make the entry stretch horizontally ---
            entry.grid(row=i + 2, column=1, pady=6, ipady=4, padx=(0, 40), sticky="ew")
            app.entry_widgets[key] = entry

    app.enroll_error_label = tk.Label(card, text="", font=font_small,
                                      fg="red", bg=LIGHT_CARD_BG)
    app.enroll_error_label.grid(row=len(fields) + 2, column=0, columnspan=2,
                                pady=(10, 0))

    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    # --- [THE FIX] Replace the text Label with a Frame containing image Labels ---
    dots_frame = tk.Frame(bf, bg=bf.cget('bg'))
    dots_frame.pack(side="left")

    # Step 1 is active
    tk.Label(dots_frame, image=app.dot_filled_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    # Steps 2 and 3 are inactive
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    # --- [END OF FIX] ---

    tk.Button(bf, text="Next Step →", font=font_button,
              bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
              command=lambda: validate_step1(app)).pack(side="right")

def validate_step1(app):
    """Validates the user registration form and sends data to the API."""
    data = {key: entry.get() for key, entry in app.entry_widgets.items()}

    if not all(v for k, v in data.items() if k != 'confirm_password'):
        app.enroll_error_label.config(text="All fields are required.")
        return

    # --- Password conditions ---
    password = data["password"]
    if len(password) < 8:
        app.enroll_error_label.config(text="Password must be at least 8 characters.")
        return
    if not any(c.isupper() for c in password):
        app.enroll_error_label.config(text="Password must contain at least one uppercase letter.")
        return
    if not any(c.islower() for c in password):
        app.enroll_error_label.config(text="Password must contain at least one lowercase letter.")
        return
    if not any(c.isdigit() for c in password):
        app.enroll_error_label.config(text="Password must contain at least one number.")
        return
    if not any(c in "!@#$%^&*()_+-=[]{};':\",.<>?/|\\`~" for c in password):
        app.enroll_error_label.config(text="Password must contain at least one special character.")
        return

    if data["password"] != data["confirm_password"]:
        app.enroll_error_label.config(text="Passwords do not match.")
        return

    # --- Call API ---
    reg_data = {k: v for k, v in data.items() if k != 'confirm_password'}
    response = app.api.register_user(reg_data)

    if response.get("status") == "success":
        app.new_enrollment_data = reg_data
        app.enroll_error_label.config(text="")
        show_enrollment_step2(app)  # proceed to next step
    else:
        app.enroll_error_label.config(text=response.get("message", "Registration failed."))


def show_enrollment_step2(app):
    """Shows the introduction screen for the voice enrollment part."""
    LIGHT_CARD_BG = "#7C2E50"

    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.enrollment_state = 'step2_voice_intro'

    import tkinter.font as tkFont
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=500, height=300, bg=LIGHT_CARD_BG)
    card.pack(pady=30)
    card.pack_propagate(False)

    tk.Label(card, text="STEP 2: Voice Authentication", font=font_title,
             fg="white", bg=LIGHT_CARD_BG).pack(anchor="w",
                                                pady=(20, 5), padx=40)

    tk.Label(card,
             text="Record your voice for added security.\nYou will record 5 phrases to create your voiceprint.",
             font=font_subtitle, fg="white", bg=LIGHT_CARD_BG,
             justify="left", wraplength=600).pack(anchor="w",
                                                  pady=(0, 25), padx=40)

    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    tk.Button(bf, text="< Back", font=font_button,
              bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR,
              relief="flat", padx=12, pady=4,
              command=lambda: show_enrollment_step1(app)).pack(side="left")

    dots_frame = tk.Frame(bf, bg=bf.cget('bg'))
    dots_frame.pack(side="left")

    tk.Label(dots_frame, image=app.dot_filled_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_filled_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)

    tk.Button(bf, text="Start →", font=font_button,
              bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR,
              relief="flat", padx=12, pady=4,
              command=lambda: show_enrollment_voice_record(app)).pack(side="right")

def show_enrollment_voice_record(app):
    """The main screen for recording the enrollment phrases."""
    LIGHT_CARD_BG = "#7C2E50"

    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.enrollment_state = 'step3_voice_record'

    import tkinter.font as tkFont
    font_title = tkFont.Font(family="Poppins", size=12, weight="bold")
    font_text = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=500, height=300, bg=LIGHT_CARD_BG)
    card.pack(pady=30)
    card.pack_propagate(False)

    tk.Label(card, text=f"{app.current_phrase_index + 1} of {len(app.enrollment_phrases)}",
             font=font_text, fg="white", bg=LIGHT_CARD_BG).pack(pady=(20, 0))

    tk.Label(card, text=f'"{app.enrollment_phrases[app.current_phrase_index]}"',
             font=font_title, fg="white", bg=LIGHT_CARD_BG,
             wraplength=600).pack(expand=True)

    mic_label = tk.Label(card, image=app.mic_img, bg=LIGHT_CARD_BG,
                         highlightthickness=0, cursor="hand2")
    mic_label.pack(pady=10)
    mic_label.bind("<Button-1>", app.toggle_recording)

    app.recording_status_label = tk.Label(card, text="Click the mic to record",
                                          font=font_text, fg="white", bg=LIGHT_CARD_BG)
    app.recording_status_label.pack(pady=(0, 20))

    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    tk.Button(bf, text="< Back", font=font_button,
              bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR,
              relief="flat", padx=12, pady=4,
              command=lambda: go_back_phrase(app)).pack(side="left")

    app.next_btn = tk.Button(bf, text="Next →", font=font_button,
                             bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR,
                             relief="flat", padx=12, pady=4,
                             command=lambda: go_next_phrase(app),
                             state="disabled")
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
        # ✅ After last phrase → upload then OTP step
        handle_final_enrollment_upload(app, next_step="otp")

def show_enrollment_step3_otp(app):
    """Shows OTP verification step after voice enrollment."""
    LIGHT_CARD_BG = "#7C2E50"

    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.enrollment_state = 'step3_otp'

    import tkinter.font as tkFont
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_entry = tkFont.Font(family="Poppins", size=11)
    font_button = tkFont.Font(family="Poppins", size=10)
    font_small = tkFont.Font(family="Poppins", size=9)

    card = tk.Frame(app.content_frame, width=500, height=250, bg=LIGHT_CARD_BG)
    card.pack(pady=40)
    card.pack_propagate(False)

    tk.Label(card, text="STEP 3: OTP Verification", font=font_title,
             fg="white", bg=LIGHT_CARD_BG).pack(anchor="w", pady=(20, 5), padx=40)

    tk.Label(card, text="Enter the 6-digit OTP code sent to your email/phone.",
             font=font_subtitle, fg="white", bg=LIGHT_CARD_BG,
             wraplength=500, justify="left").pack(anchor="w", padx=40, pady=(0, 15))

    app.otp_entry = tk.Entry(card, font=font_entry, width=16,
                             bg="white", fg="black", relief="flat", bd=0,
                             justify="center", insertbackground="black")
    app.otp_entry.pack(pady=(0, 10))

    app.otp_error_label = tk.Label(card, text="", font=font_small,
                                   fg="red", bg=LIGHT_CARD_BG)
    app.otp_error_label.pack()

    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 20))

    tk.Button(bf, text="< Back", font=font_button,
              bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR,
              relief="flat", padx=12, pady=4,
              command=lambda: show_enrollment_voice_record(app)).pack(side="left")

    dots_frame = tk.Frame(bf, bg=bf.cget('bg'))
    dots_frame.pack(side="left")
    tk.Label(dots_frame, image=app.dot_filled_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_filled_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_filled_img, bg=bf.cget('bg')).pack(side="left", padx=2)

    tk.Button(bf, text="Verify →", font=font_button,
              bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR,
              relief="flat", padx=20, pady=4,
              command=lambda: validate_otp(app)).pack(side="right")

def validate_otp(app):
    """Validates the OTP entered by the user."""
    otp_code = app.otp_entry.get().strip()

    # 🛠 FIX: ensure exactly 6 digits, walang ibang char
    if not otp_code.isdigit() or len(otp_code) != 6:
        app.otp_error_label.config(text="Please enter a valid 6-digit OTP.")
        return

    # ✅ send to backend
    response = app.api.verify_otp(app.new_enrollment_data.get("username"), otp_code)

    if response.get("status") == "success":
        app.otp_error_label.config(text="")
        show_enrollment_summary(app)  # proceed to summary
    else:
        app.otp_error_label.config(text=response.get("message", "Invalid OTP."))


def handle_final_enrollment_upload(app, next_step="summary"):
    """Uploads the primary voice recording to the backend."""
    username = app.new_enrollment_data.get("username")
    filepath = os.path.join(config.AUDIO_DIR, f"{username}_phrase_1.wav")

    if not os.path.exists(filepath):
        messagebox.showerror("Error", "Primary enrollment audio not found. Please record phrase 1 again.")
        return

    response = app.api.enroll_voice(username, filepath)
    if response.get("status") == "success":
        if next_step == "otp":
            show_enrollment_step3_otp(app)  # ✅ proceed to OTP step muna
        else:
            show_enrollment_summary(app)
    else:
        messagebox.showerror("Enrollment Failed", response.get("message", "Final enrollment failed."))


def show_enrollment_summary(app):
    """Displays a summary of the successfully enrolled user's details."""
    LIGHT_CARD_BG = "#7C2E50"

    for widget in app.content_frame.winfo_children():
        widget.destroy()

    import tkinter.font as tkFont
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_text = tkFont.Font(family="Poppins", size=11)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=500, height=300, bg=LIGHT_CARD_BG)
    card.pack(pady=30)
    card.pack_propagate(False)

    tk.Label(card, text="Enrollment Process Complete", font=font_title,
             fg="white", bg=LIGHT_CARD_BG).grid(row=0, column=0, columnspan=2,
                                               sticky="w", pady=(20, 5), padx=40)
    tk.Label(card,
             text="You've successfully enrolled. Your credentials are now securely registered.",
             font=font_text, fg="white", bg=LIGHT_CARD_BG, justify="left",
             wraplength=600).grid(row=1, column=0, columnspan=2, sticky="w",
                                  pady=(0, 25), padx=40)

    summary_data = {
        "Full Name:": app.new_enrollment_data.get('full_name'),
        "Username:": app.new_enrollment_data.get('username'),
        "Password:": '********',
        "Email:": app.new_enrollment_data.get('email'),
        "Voice Pattern:": "Saved"
    }

    for i, (label, value) in enumerate(summary_data.items()):
        tk.Label(card, text=label, font=font_text,
                 fg="white", bg=LIGHT_CARD_BG).grid(row=i + 2, column=0,
                                                    sticky="w", pady=5, padx=40)
        tk.Label(card, text=value, font=font_text,
                 fg="white", bg=LIGHT_CARD_BG).grid(row=i + 2, column=1,
                                                    sticky="w", pady=5, padx=20)

    tk.Button(card, text="Finish", font=font_button,
              bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR,
              relief="flat", padx=30, pady=5,
              command=app._finish_enrollment).grid(row=len(summary_data) + 2,
                                                   column=0, columnspan=2,
                                                   pady=30)


def finish_enrollment(app):
    """Finalizes enrollment and redirects to the home screen for login."""
    messagebox.showinfo("Success", "New user enrollment complete! Please log in.")
    app.just_enrolled_username = app.new_enrollment_data.get("username")
    app.just_enrolled = True
    app.enrollment_state = 'not_started'
    app.show_home_screen()