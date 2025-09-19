import tkinter as tk
from tkinter import font, messagebox
import frontend_config as config
from . import ui_helpers

def show_applications_screen(app):
    """Shows the application management screen for a logged-in user."""
    ui_helpers.update_nav_selection(app, "applications")
    if not app.currently_logged_in_user:
        card = ui_helpers.create_main_card(app, width=600, height=300)
        tk.Label(card, text="Please log in to manage application settings.", font=app.font_large, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR, wraplength=400).pack(expand=True)
        return
    
    user = app.currently_logged_in_user
    card = ui_helpers.create_main_card(app, width=780, height=380)
    cards_frame = tk.Frame(card, bg=config.CARD_BG_COLOR)
    cards_frame.pack(expand=True)
    
    # Helper to create the cards
    def _create_app_card(parent):
        c = tk.Frame(parent, bg=config.CARD_BG_COLOR, width=220, height=280, relief="solid", bd=1)
        c.pack(side="left", padx=15, pady=20)
        c.pack_propagate(False)
        return c

    # Password Card
    pw_card = _create_app_card(cards_frame)
    tk.Label(pw_card, image=app.key_img, bg=config.CARD_BG_COLOR).pack(pady=(20, 0))
    tk.Label(pw_card, text="Password", font=app.font_medium_bold, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=(10, 5))
    tk.Label(pw_card, text="********", font=app.font_large, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=5)
    tk.Button(pw_card, text="Edit Password", font=app.font_small, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="solid", bd=1, padx=10, command=lambda: messagebox.showinfo("Info", "Password management is a future feature.")).pack(side=tk.BOTTOM, pady=(10, 15))
    
    # Voice Biometrics Card
    voice_status = "Enrolled" if user.get('voiceprint_path') else "Not Enrolled"
    voice_card = _create_app_card(cards_frame)
    tk.Label(voice_card, image=app.mic_img, bg=config.CARD_BG_COLOR).pack(pady=(20, 0))
    tk.Label(voice_card, text="Voice Biometrics", font=app.font_medium_bold, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=(10, 5))
    tk.Label(voice_card, text=f"Status: {voice_status}", font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=5)
    tk.Button(voice_card, text="Edit Biometrics", font=app.font_small, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="solid", bd=1, padx=10, command=app.navigate_to_enrollment).pack(side=tk.BOTTOM, pady=(10, 15))
    
    # OTP Settings Card
    masked_email = app._mask_email(user.get('email', ''))
    otp_card = _create_app_card(cards_frame)
    tk.Label(otp_card, image=app.otp_img, bg=config.CARD_BG_COLOR).pack(pady=(20, 0))
    tk.Label(otp_card, text="OTP Settings", font=app.font_medium_bold, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=(10, 5))
    tk.Label(otp_card, text="Account:", font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=(5, 0))
    tk.Label(otp_card, text=masked_email, font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=(0, 5))
    tk.Button(otp_card, text="Edit Email Address", font=app.font_small, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="solid", bd=1, padx=10, command=lambda: messagebox.showinfo("Info", "Email management is a future feature.")).pack(side=tk.BOTTOM, pady=(10, 15))


def show_about_screen(app, event=None):
    """Displays the About Us screen."""
    ui_helpers.update_nav_selection(app, None)
    INFO_CARD_BG, INFO_CARD_TEXT = "#e9e3e6", "#3b3b3b"
    card = ui_helpers.create_main_card(app, width=820, height=480)
    card.config(bg=INFO_CARD_BG, relief="flat", bd=0, highlightthickness=0)
    
    content_frame = tk.Frame(card, bg=INFO_CARD_BG)
    content_frame.pack(expand=True)
    
    title_font = font.Font(family=config.FONT_FAMILY, size=22, weight="bold")
    tk.Label(content_frame, text="About Us", font=title_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left").pack(anchor="w", pady=(0, 20))
    
    body_font = font.Font(family=config.FONT_FAMILY, size=12)
    about_text = "KeyVox is a new plug-and-play hardware authentication token that uses your unique voice as a robust and secure second factor of authentication (2FA), powered by advanced LSTM neural networks. The key is designed to work with multi-protocol systems such as FIDO U2F, OATH TOTP, challenge response system."
    tk.Label(content_frame, text=about_text, font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left", wraplength=720).pack(anchor="w", pady=(0, 30))
    
    subtitle_font = font.Font(family=config.FONT_FAMILY, size=16, weight="bold")
    tk.Label(content_frame, text="How Voice Authentication Works", font=subtitle_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left").pack(anchor="w", pady=(0, 15))
    tk.Label(content_frame, text="KeyVox uses LSTM-based voice biometrics to:", font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left").pack(anchor="w", pady=(0, 10))
    
    bullets = ["Analyze and learn the unique patterns in your voice.", "Match live voice input against your stored encrypted voiceprint.", "Authenticate only if the match is within the secure threshold."]
    for bullet in bullets:
        tk.Label(content_frame, text=f"  •  {bullet}", font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left", wraplength=700).pack(anchor="w", pady=2)


def show_help_screen(app, event=None):
    """Displays the Help/FAQ screen."""
    ui_helpers.update_nav_selection(app, None)
    INFO_CARD_BG, INFO_CARD_TEXT = "#e9e3e6", "#3b3b3b"
    card = ui_helpers.create_main_card(app, width=820, height=480)
    card.config(bg=INFO_CARD_BG, relief="flat", bd=0, highlightthickness=0)
    
    content_frame = tk.Frame(card, bg=INFO_CARD_BG)
    content_frame.pack(expand=True)
    content_frame.grid_columnconfigure(0, weight=1)
    content_frame.grid_columnconfigure(1, weight=1)
    
    title_font = font.Font(family=config.FONT_FAMILY, size=22, weight="bold")
    tk.Label(content_frame, text="Need Help?", font=title_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 25))
    
    # Left Column
    left_frame = tk.Frame(content_frame, bg=INFO_CARD_BG)
    left_frame.grid(row=1, column=0, sticky="nw", padx=(0, 20))
    subtitle_font = font.Font(family=config.FONT_FAMILY, size=16, weight="bold")
    tk.Label(left_frame, text="Setup Instructions", font=subtitle_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG).pack(anchor="w", pady=(0, 15))
    
    setup_steps = ["Connect KeyVox to your computer via USB.", "Open the KeyVox App (pre-installed or downloadable).", "Follow the voice enrollment process.", "You will be asked to record a short phrase 3-5 times in a quiet environment. The system will use these samples to create a secure voiceprint.", "Set up your preferred authentication protocols: Choose between FIDO, OATH, or challenge response options depending on the services you want to link."]
    body_font = font.Font(family=config.FONT_FAMILY, size=12)
    for i, step in enumerate(setup_steps, 1):
        tk.Label(left_frame, text=f"{i}. {step}", font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left", wraplength=350).pack(anchor="w", pady=4)
        
    # Right Column
    right_frame = tk.Frame(content_frame, bg=INFO_CARD_BG)
    right_frame.grid(row=1, column=1, sticky="nw", padx=(20, 0))
    tk.Label(right_frame, text="Security Tips", font=subtitle_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG).pack(anchor="w", pady=(0, 15))
    
    security_tips = ["Enroll in a quiet environment for better accuracy.", "Update your voice model if you're sick or your voice changes significantly.", "Never share recordings of your voice used for authentication."]
    for i, tip in enumerate(security_tips, 1):
        tk.Label(right_frame, text=f"{i}. {tip}", font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left", wraplength=350).pack(anchor="w", pady=4)