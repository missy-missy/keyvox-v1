# In your ui/application_settings.py file

import tkinter as tk
from . import ui_helpers
import frontend_config as config
import os
from tkinter import messagebox
from PIL import Image, ImageTk

def load_images(app):
    """Load and resize all images used in the UI."""
    # Eye icons for password toggle
    eye_open = Image.open("assets/eye_open.png").resize((24, 24), Image.ANTIALIAS)
    eye_closed = Image.open("assets/eye_closed.png").resize((24, 24), Image.ANTIALIAS)
    app.eye_open_img = ImageTk.PhotoImage(eye_open)
    app.eye_closed_img = ImageTk.PhotoImage(eye_closed)

    # Microphone icon for voice enrollment
    mic = Image.open("assets/mic.png").resize((40, 40), Image.ANTIALIAS)
    app.mic_img = ImageTk.PhotoImage(mic)

# In your ui/application_settings.py file
"--------------- CHANGE PASSWORD ------------------------ "
def show_change_password_screen(app):
    """
    Simplified Change Password screen:
    Only asks for Current, New, and Confirm Password.
    Proceeds directly to OTP verification after saving.
    """
    LIGHT_CARD_BG = "#AD567C"

    # --- Clear old widgets ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    import tkinter as tk
    from tkinter import messagebox, font as tkFont

    # --- Fonts ---
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_label = tkFont.Font(family="Poppins", size=11)
    font_entry = tkFont.Font(family="Poppins", size=11)
    font_small = tkFont.Font(family="Poppins", size=9)
    font_button = tkFont.Font(family="Poppins", size=10)

    # --- Card container ---
    card = tk.Frame(app.content_frame, width=700, height=400, bg=LIGHT_CARD_BG)
    card.pack(pady=30)
    card.pack_propagate(False)

    # --- Title ---
    tk.Label(
        card,
        text="Change Password",
        font=font_title,
        fg="white",
        bg=LIGHT_CARD_BG
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(20, 5), padx=40)

    # --- Subtitle ---
    tk.Label(
        card,
        text="Enter your account information below",
        font=font_subtitle,
        fg="white",
        bg=LIGHT_CARD_BG
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 20), padx=40)

    # --- Password Fields ---
    fields = {
        "Current Password:": "current_password",
        "New Password:": "new_password",
        "Confirm Password:": "confirm_password"
    }

    app.entry_widgets = {}

    def make_password_field(parent, label_text, key, row):
        tk.Label(parent, text=label_text, font=font_label,
                 fg="white", bg=LIGHT_CARD_BG).grid(row=row, column=0,
                                                    sticky="w", pady=6, padx=(40, 20))

        entry_frame = tk.Frame(parent, bg="white")
        entry_frame.grid(row=row, column=1, pady=6, ipady=4, padx=(0, 40))

        entry = tk.Entry(entry_frame, font=font_entry, width=22,
                         bg="white", fg="black", relief="flat", bd=0,
                         show="*", insertbackground="black")
        entry.pack(side="left", ipady=4, padx=(5, 0))
        app.entry_widgets[key] = entry

        # Eye toggle (optional, requires images)
        if hasattr(app, "eye_open_img") and hasattr(app, "eye_closed_img"):
            def toggle_visibility():
                if entry.cget("show") == "*":
                    entry.config(show="")
                    btn.config(image=app.eye_closed_img)
                else:
                    entry.config(show="*")
                    btn.config(image=app.eye_open_img)

            btn = tk.Button(entry_frame, image=app.eye_open_img, bg="white",
                            relief="flat", bd=0, activebackground="white",
                            cursor="hand2", command=toggle_visibility)
            btn.pack(side="right", padx=(0, 5))

    for i, (label, key) in enumerate(fields.items(), start=2):
        make_password_field(card, label, key, i)

    # --- Error/Info Label ---
    app.enroll_error_label = tk.Label(
        card, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG
    )
    app.enroll_error_label.grid(row=len(fields) + 2, column=0, columnspan=2, pady=(10, 0))

    # --- Footer buttons ---
    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    # Back button
    tk.Button(
        bf, text="Back", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
        command=lambda: app.show_applications_screen()
    ).pack(side="left")

    # Save Changes button → straight to OTP
    def dummy_save_password():
        data = {key: entry.get() for key, entry in app.entry_widgets.items()}

        # Basic validation
        if not all(data.values()):
            app.enroll_error_label.config(text="All fields are required.")
            return
        if data["new_password"] != data["confirm_password"]:
            app.enroll_error_label.config(text="New passwords do not match.")
            return

        messagebox.showinfo("Success", "Password updated (dummy). Proceeding to OTP...")
        app.show_applications_screen()

    tk.Button(
        bf, text="Save Changes", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
        command=dummy_save_password
    ).pack(side="right")


"--------------- CHANGE VOICE BIOMETRICS ------------------------ "
# -------------------------------
# Step 1: Password Entry
# -------------------------------
def check_password(app):
    """Bypass password check: always allow proceeding."""
    # If no currently logged in user, set a dummy one
    if not app.currently_logged_in_user:
        app.currently_logged_in_user = {
            "username": "dummy_user",
            "email": "dummy@example.com"
        }
    # Proceed to OTP verification screen
    show_voice_enrollment_screen(app)

def show_password_screen_voice_entry1(app):
    """
    Shows the password entry screen with the correct design, visibility toggle,
    and always bypasses password validation.
    """
    app.login_flow_state = 'password_entry'
    LIGHT_CARD_BG = "#AD567C"

    # --- Card ---
    card = ui_helpers.create_main_card(app, width=420, height=300)
    card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)

    content_wrapper = tk.Frame(card, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
    content_wrapper.pack(expand=True)

    # --- Title ---
    tk.Label(
        content_wrapper,
        text="Enter Password",
        font=app.font_large,
        fg="white",
        bg=LIGHT_CARD_BG
    ).pack(pady=(20, 10))

    # --- Error Label ---
    app.error_label = tk.Label(
        content_wrapper,
        text="",
        font=app.font_small,
        fg=config.ERROR_COLOR,
        bg=LIGHT_CARD_BG
    )
    app.error_label.pack(pady=(0, 10))

    # --- Entry + Eye Icon ---
    entry_frame = tk.Frame(content_wrapper, bg="white")
    entry_frame.pack(pady=10)

    app.password_entry = tk.Entry(
        entry_frame,
        font=app.font_large,
        fg="black",
        bg="white",
        show="*",
        width=22,
        relief="flat",
        bd=0,
        justify="center",
        insertbackground="black"
    )
    app.password_entry.pack(side="left", ipady=5, padx=(10, 0))
    app.password_entry.focus_set()

    def toggle_password_visibility():
        if app.password_entry.cget('show') == '*':
            app.password_entry.config(show='')
            eye_button.config(image=app.eye_closed_img)
        else:
            app.password_entry.config(show='*')
            eye_button.config(image=app.eye_open_img)

    eye_button = tk.Button(
        entry_frame,
        image=app.eye_open_img,
        bg="white",
        relief="flat",
        bd=0,
        activebackground="white",
        command=toggle_password_visibility,
        cursor="hand2"
    )
    eye_button.pack(side="right", padx=(0, 5))

    # --- Validation function (always bypass) ---
    def validate_and_submit():
        """Bypass password check and go to OTP verification."""
        app.error_label.config(text="")  # clear any previous error
        check_password(app)  # directly go to OTP

    # --- Rounded Confirm Button ---
    def create_rounded_button(parent, text, command=None, radius=15, width=200, height=40, bg="#F5F5F5", fg="black"):
        wrapper = tk.Frame(parent, bg=LIGHT_CARD_BG)
        wrapper.pack(pady=(20, 15))

        canvas = tk.Canvas(wrapper, width=width, height=height, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0, relief="flat", cursor="hand2")
        canvas.pack()

        x1, y1, x2, y2 = 2, 2, width-2, height-2
        canvas.create_oval(x1, y1, x1 + radius*2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y1, x2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x1, y2 - radius*2, x1 + radius*2, y2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y2 - radius*2, x2, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=bg, outline=bg)

        btn_text = canvas.create_text(width//2, height//2, text=text, fill=fg, font=app.font_normal)

        def on_click(event):
            if command:
                command()
        canvas.tag_bind(btn_text, "<Button-1>", on_click)
        canvas.bind("<Button-1>", on_click)

        return wrapper

    create_rounded_button(content_wrapper, "Confirm Login", command=validate_and_submit)


# -------------------------------
# Step 2: Voice Enrollment (Frontend only)
# -------------------------------
def show_voice_enrollment_screen(app):
    """Voice enrollment screen (frontend only)."""
    LIGHT_CARD_BG = "#AD567C"

    # Clear old widgets
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    import tkinter.font as tkFont
    import random
    from tkinter import messagebox
    from .other_screens import show_applications_screen  # make sure this import path is correct

    font_title = tkFont.Font(family="Poppins", size=12, weight="bold")
    font_text = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=10)

    # Sample phrases
    phrases = [
        "The quick brown fox jumps over the lazy dog.",
        "Secure authentication keeps data safe.",
        "My voice is my password.",
        "Artificial Intelligence is shaping the future.",
        "Open the door with my unique voice."
    ]
    phrase_to_read = random.choice(phrases)

    card = tk.Frame(app.content_frame, width=500, height=300, bg=LIGHT_CARD_BG)
    card.pack(pady=30)
    card.pack_propagate(False)

    tk.Label(card, text="Voice Enrollment", font=font_title, fg="white", bg=LIGHT_CARD_BG).pack(pady=(20, 10))
    tk.Label(card, text='Please read the phrase aloud:', font=font_text, fg="white", bg=LIGHT_CARD_BG).pack()
    tk.Label(card, text=f'"{phrase_to_read}"', font=font_text, fg="yellow", bg=LIGHT_CARD_BG, wraplength=450).pack(expand=True, pady=10)

    # Mic button
    mic_label = tk.Label(card, image=app.mic_img, bg=LIGHT_CARD_BG, highlightthickness=0, cursor="hand2")
    mic_label.pack(pady=10)
    mic_label.bind("<Button-1>", lambda e: app.recording_status_label.config(text="Recording..."))

    # Status label
    app.recording_status_label = tk.Label(card, text="Click the mic to record", font=font_text, fg="white", bg=LIGHT_CARD_BG)
    app.recording_status_label.pack(pady=(0, 20))

    # Footer buttons
    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    tk.Button(bf, text="< Back", font=font_button, bg="#F5F5F5", fg="black",
              relief="flat", padx=12, pady=4, command=lambda: show_otp_verification_screen(app)).pack(side="left")

    def complete_enrollment():
        messagebox.showinfo("Success", "Voice enrollment complete!")
        show_applications_screen(app)

    tk.Button(bf, text="Next →", font=font_button, bg="#F5F5F5", fg="black",
              relief="flat", padx=12, pady=4, command=complete_enrollment).pack(side="right")


"--------------- CHANGE OTP Email Address ------------------------ "
# ------ dating show_otp_settings_screen_step 2 and new name lang siya ------
def show_change_otp_settings_screen(app):
    """Displays the OTP settings screen with confirm email + proceed to OTP verification."""
    LIGHT_CARD_BG = "#AD567C"

    # Clear old widgets
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    import tkinter.font as tkFont
    from tkinter import messagebox

    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_label = tkFont.Font(family="Poppins", size=11)
    font_entry = tkFont.Font(family="Poppins", size=11)
    font_small = tkFont.Font(family="Poppins", size=9)
    font_button = tkFont.Font(family="Poppins", size=10)

    # --- Card container ---
    card = tk.Frame(app.content_frame, width=700, height=400, bg=LIGHT_CARD_BG)
    card.pack(pady=30)
    card.pack_propagate(False)

    # --- Title & subtitle ---
    tk.Label(card, text="Edit OTP Settings", font=font_title, fg="white", bg=LIGHT_CARD_BG).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(20, 5), padx=40
    )
    tk.Label(card, text="Enter your email address and confirm it before verifying with OTP.",
             font=font_subtitle, fg="white", bg=LIGHT_CARD_BG).grid(
        row=1, column=0, columnspan=2, sticky="w", pady=(0, 20), padx=40
    )

    # --- Fields ---
    fields = {
        "New Email Address:": "email_address",
        "Confirm Email Address:": "confirm_email"
    }

    app.entry_widgets = {}
    for i, (label, key) in enumerate(fields.items()):
        tk.Label(card, text=label, font=font_label, fg="white", bg=LIGHT_CARD_BG).grid(
            row=i + 2, column=0, sticky="w", pady=6, padx=(40, 20)
        )

        entry = tk.Entry(card, font=font_entry, width=30, bg="white", fg="black",
                         relief="flat", bd=0, insertbackground="black")
        entry.grid(row=i + 2, column=1, pady=6, ipady=4, padx=(0, 40))
        app.entry_widgets[key] = entry

    # --- Error label ---
    app.enroll_error_label = tk.Label(card, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG)
    app.enroll_error_label.grid(row=len(fields) + 2, column=0, columnspan=2, pady=(10, 0))

    # --- Footer buttons ---
    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    # Back button
    tk.Button(
        bf, text="Back", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
        command=lambda: app.show_applications_screen()
    ).pack(side="left")

    # Proceed button (dummy for now)
    def proceed_to_otp():
        email = app.entry_widgets["email_address"].get().strip()
        confirm = app.entry_widgets["confirm_email"].get().strip()
        if not email or not confirm:
            app.enroll_error_label.config(text="All fields are required.")
            return
        if email != confirm:
            app.enroll_error_label.config(text="Email addresses do not match.")
            return
        # success → go to OTP verification (dummy)
        show_change_otp_settings_verification_screen(app)

    tk.Button(
        bf, text="Proceed", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
        command=proceed_to_otp
    ).pack(side="right")

def show_change_otp_settings_verification_screen(app):
    """Shows a styled OTP verification screen with dummy bypass and proper bottom margin."""
    LIGHT_CARD_BG = "#AD567C"

    # Clear old widgets
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    import tkinter.font as tkFont
    from .other_screens import show_applications_screen
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_text = tkFont.Font(family="Poppins", size=12)
    font_small = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=11)

    # --- Card ---
    card = tk.Frame(app.content_frame, width=420, height=280, bg=LIGHT_CARD_BG)
    card.pack(pady=(30, 20))  # 30px top, 20px bottom
    card.pack_propagate(False)

    # --- Title ---
    tk.Label(card, text="OTP Verification", font=font_title, fg="white", bg=LIGHT_CARD_BG).pack(pady=(20, 10))

    # --- Info Text ---
    email = app.currently_logged_in_user.get('email', 'your_email@example.com') if app.currently_logged_in_user else 'your_email@example.com'
    tk.Label(card, text=f"Enter the 6-digit code sent to {email}", font=font_small, fg="white", bg=LIGHT_CARD_BG, wraplength=380).pack(pady=(0, 15))

    # --- OTP Entry ---
    app.otp_entry = tk.Entry(card, font=font_text, width=20, justify="center")
    app.otp_entry.pack(ipady=6, pady=(0, 10))

    # --- Error Label ---
    app.otp_error_label = tk.Label(card, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG)
    app.otp_error_label.pack(pady=(0, 10))

    # --- Send Code Label ---
    tk.Label(card, text="Didn't Receive Code?", font=font_small, fg="white", bg=LIGHT_CARD_BG, wraplength=380).pack(pady=(0, 5))

    # --- Send Code Button ---
    def send_code():
        messagebox.showinfo("Send Code", f"OTP code sent to {email}")

    tk.Button(card, text="Send Code", font=font_small, command=send_code, bg="#F5F5F5").pack(pady=(0, 10))

    # --- Verify Function (bypasses OTP for testing) ---
    def verify_otp():
        # Always allow for testing
        show_applications_screen(app)

    # --- Rounded Verify Button ---
    def create_rounded_button(parent, text, command=None, radius=15, width=200, height=40, bg="#F5F5F5", fg="black"):
        wrapper = tk.Frame(parent, bg=LIGHT_CARD_BG)
        wrapper.pack(pady=0)  # spacing handled by wrapper frame below

        canvas = tk.Canvas(wrapper, width=width, height=height, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0, relief="flat", cursor="hand2")
        canvas.pack()

        x1, y1, x2, y2 = 2, 2, width-2, height-2
        canvas.create_oval(x1, y1, x1 + radius*2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y1, x2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x1, y2 - radius*2, x1 + radius*2, y2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y2 - radius*2, x2, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=bg, outline=bg)

        btn_text = canvas.create_text(width//2, height//2, text=text, fill=fg, font=app.font_normal)

        def on_click(event):
            if command:
                command()
        canvas.tag_bind(btn_text, "<Button-1>", on_click)
        canvas.bind("<Button-1>", on_click)

        return wrapper

    # --- Place the button below the card with proper bottom margin ---
    button_wrapper = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    button_wrapper.pack(pady=(0, 30))  # 30px bottom margin
    create_rounded_button(button_wrapper, "Verify OTP", command=verify_otp)