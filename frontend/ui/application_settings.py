# In your ui/application_settings.py file

import tkinter as tk
from . import ui_helpers
import frontend_config as config

# In your ui/application_settings.py file

def show_change_password_screen(app):
    """
    Change password screen with modern card + rounded button style,
    consistent with the Applications page design.
    """

    LIGHT_CARD_BG = "#7C2E50"

    # --- Clear old widgets ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

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

    tk.Label(card, text="Change Password", font=font_title,
             fg="white", bg=LIGHT_CARD_BG).grid(row=0, column=0, columnspan=2,
                                               sticky="w", pady=(20, 5), padx=40)
    tk.Label(card, text="Enter your account information below",
             font=font_subtitle, fg="white", bg=LIGHT_CARD_BG).grid(row=1, column=0,
                                                                   columnspan=2,
                                                                   sticky="w",
                                                                   pady=(0, 20),
                                                                   padx=40)

    fields = {
        "Current Password:": "current_password",
        "New Password:": "new_password",
        "Confirm Password:": "confirm_password"
    }

    app.entry_widgets = {}
    for i, (label, key) in enumerate(fields.items()):
        tk.Label(card, text=label, font=font_label,
                 fg="white", bg=LIGHT_CARD_BG).grid(row=i + 2, column=0,
                                                    sticky="w", pady=6,
                                                    padx=(40, 20))

        entry = tk.Entry(card, font=font_entry, width=25,
                         bg="white", fg="black", relief="flat", bd=0,
                         insertbackground="black")
        app.entry_widgets[key] = entry
        if "Password" in label:
            entry.config(show="*")
        entry.grid(row=i + 2, column=1, pady=6, ipady=4, padx=(0, 40))

    app.enroll_error_label = tk.Label(card, text="", font=font_small,
                                      fg="red", bg=LIGHT_CARD_BG)
    app.enroll_error_label.grid(row=len(fields) + 2, column=0, columnspan=2,
                                pady=(10, 0))

    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    # Back button (return to previous screen)
    tk.Button(bf, text="Back", font=font_button,
              bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
              command=lambda: app.show_applications_screen()).pack(side="left")

    # Save Changes button (validate change password)
    tk.Button(bf, text="Save Changes", font=font_button,
              bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
              command=lambda: app.show_applications_screen(app)).pack(side="right")


def validate_change_password(app):
    """Logic for verifying current password and updating to new one."""

    data = {key: entry.get() for key, entry in app.entry_widgets.items()}

    # 1. Check all fields filled
    if not all(data.values()):
        app.enroll_error_label.config(text="All fields are required.")
        return

    # 2. New password and confirm must match
    if data["new_password"] != data["confirm_password"]:
        app.enroll_error_label.config(text="New passwords do not match.")
        return

    # 3. Call API to verify current password and update
    payload = {
        "current_password": data["current_password"],
        "new_password": data["new_password"]
    }
    response = app.api.change_password(payload)

    if response.get("status") == "success":
        app.enroll_error_label.config(text="", fg="green")
        messagebox.showinfo("Success", "Your password has been updated successfully!")
        app.show_login_voice_auth_screen()  # redirect to login after change
    else:
        app.enroll_error_label.config(text=response.get("message", "Password change failed."))
    
def show_edit_biometrics_screen(app):
    """Displays the biometrics page with a modern card + footer button design."""
    LIGHT_CARD_BG = "#7C2E50"

    # --- Clear old widgets ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    import tkinter.font as tkFont
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
        text="Edit Voice Biometrics",
        font=font_title,
        fg="white",
        bg=LIGHT_CARD_BG
    ).grid(row=0, column=0, columnspan=2,
           sticky="w", pady=(20, 5), padx=40)

    # --- Subtitle ---
    tk.Label(
        card,
        text="Re-enroll your voice to update biometrics.",
        font=font_subtitle,
        fg="white",
        bg=LIGHT_CARD_BG
    ).grid(row=1, column=0, columnspan=2,
           sticky="w", pady=(0, 20), padx=40)

    # --- Placeholder for extra info (optional) ---
    tk.Label(
        card,
        text="This will replace your old voice data with new recordings.",
        font=font_small,
        fg="white",
        bg=LIGHT_CARD_BG
    ).grid(row=2, column=0, columnspan=2,
           sticky="w", pady=(0, 10), padx=40)

    # --- Footer buttons ---
    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    # Back button
    tk.Button(
        bf, text="Back", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
        command=lambda: app.show_applications_screen()
    ).pack(side="left")

    # Re-Enroll button
    tk.Button(
        bf, text="Re-Enroll Voice", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
        command=lambda: app.show_enrollment_voice_record()
    ).pack(side="right")


def show_otp_settings_screen(app):
    """Displays the OTP page with the simple, flat card design."""
    LIGHT_CARD_BG = "#7C2E50"

    # --- Clear old widgets ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    import tkinter.font as tkFont
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
        text="Edit OTP Settings",
        font=font_title,
        fg="white",
        bg=LIGHT_CARD_BG
    ).grid(row=0, column=0, columnspan=2,
           sticky="w", pady=(20, 5), padx=40)

    # --- Subtitle ---
    tk.Label(
        card,
        text="Change your email address and verify with code.",
        font=font_subtitle,
        fg="white",
        bg=LIGHT_CARD_BG
    ).grid(row=1, column=0, columnspan=2,
           sticky="w", pady=(0, 20), padx=40)

    # --- Fields ---
    fields = {
        "Email Address:": "email_address",
        "Password:": "password"
    }

    app.entry_widgets = {}
    for i, (label, key) in enumerate(fields.items()):
        tk.Label(card, text=label, font=font_label,
                 fg="white", bg=LIGHT_CARD_BG).grid(row=i + 2, column=0,
                                                    sticky="w", pady=6,
                                                    padx=(40, 20))

        entry = tk.Entry(card, font=font_entry, width=30,
                         bg="white", fg="black", relief="flat", bd=0,
                         insertbackground="black")
        if "Password" in label:
            entry.config(show="*")
        entry.grid(row=i + 2, column=1, pady=6, ipady=4, padx=(0, 40))
        app.entry_widgets[key] = entry

    # --- Error label (for invalid inputs) ---
    app.enroll_error_label = tk.Label(
        card, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG
    )
    app.enroll_error_label.grid(row=len(fields) + 2, column=0, columnspan=2,
                                pady=(10, 0))

    # --- Footer buttons ---
    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    # Back button
    tk.Button(
        bf, text="Back", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
        command=lambda: app.show_applications_screen()
    ).pack(side="left")

    # Get Code button
    tk.Button(
        bf, text="Get Code", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
        command=lambda: validate_otp_settings(app)
    ).pack(side="right")


def validate_otp_settings(app):
    """Handles logic for OTP settings (email + password check)."""
    email = app.entry_widgets["email_address"].get().strip()
    password = app.entry_widgets["password"].get().strip()

    if not email or not password:
        app.enroll_error_label.config(text="All fields are required.")
        return

    # Example call (you need to connect this with your API client)
    try:
        response = app.api.request_otp(email=email, password=password)
        if response.get("success"):
            app.show_otp_verification_screen()  # placeholder for next step
        else:
            app.enroll_error_label.config(text=response.get("error", "Failed to request OTP."))
    except Exception as e:
        app.enroll_error_label.config(text=f"Error: {e}")