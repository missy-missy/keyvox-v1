import tkinter as tk
from tkinter import font, messagebox
import frontend_config as config
from . import ui_helpers
from PIL import Image, ImageTk

def show_applications_screen(app):
    """Shows the application management screen for a logged-in user with modern card + rounded button style."""
    ui_helpers.update_nav_selection(app, "applications")

    LIGHT_CARD_BG = "#7C2E50"

    card = ui_helpers.create_main_card(app, width=820, height=420)
    card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
    card.pack(expand=True, fill="both")   
    # If not logged in
    if not app.currently_logged_in_user:
        card = ui_helpers.create_main_card(app, width=600, height=300)
        card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)

        tk.Label(
            card,
            text="Please log in to manage application settings.",
            font=app.font_large,
            fg=config.TEXT_COLOR,
            bg=LIGHT_CARD_BG,
            wraplength=400
        ).pack(expand=True)
        return

    user = app.currently_logged_in_user

    # --- Main Card ---
    card = ui_helpers.create_main_card(app, width=820, height=420)
    card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)

    # Title
    tk.Label(
        card,
        text="Manage Applications",
        font=app.font_large,
        fg=config.TEXT_COLOR,
        bg=LIGHT_CARD_BG
    ).pack(pady=(20, 10))

    # Wrapper for cards
    cards_frame = tk.Frame(card, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
    cards_frame.pack(expand=True, pady=10)

    # --- Helper to create consistent cards ---
    def _create_app_card(parent, icon, title, details, button_text, button_command):
        c = tk.Frame(parent, bg=config.CARD_BG_COLOR, width=230, height=300, relief="flat", bd=0)
        c.pack(side="left", padx=15, pady=10)
        c.pack_propagate(False)

        # Icon
        tk.Label(c, image=icon, bg=config.CARD_BG_COLOR).pack(pady=(20, 10))
        # Title
        tk.Label(c, text=title, font=app.font_medium_bold, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack()
        # Details
        for line in details:
            tk.Label(c, text=line, font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR, wraplength=200).pack(pady=3)

        # Button
        tk.Button(
            c,
            text=button_text,
            font=app.font_small,
            bg=config.BUTTON_LIGHT_COLOR,
            fg=config.BUTTON_LIGHT_TEXT_COLOR,
            relief="flat",
            padx=12, pady=6,
            command=button_command
        ).pack(side=tk.BOTTOM, pady=15)

        return c

    # --- Password Card ---
    _create_app_card(
        cards_frame,
        app.key_img,
        "Password",
        ["********"],
        "Edit Password",
        app.show_change_password_screen
    )

    # --- Voice Biometrics Card ---
    voice_status = "Enrolled" if user.get('voiceprint_path') else "Not Enrolled"
    _create_app_card(
        cards_frame,
        app.mic_img,
        "Voice Biometrics",
        [f"Status: {voice_status}"],
        "Edit Biometrics",
        app.show_password_screen_voice_entry1
    )

    # --- OTP Settings Card ---
    masked_email = app._mask_email(user.get('email', ''))
    _create_app_card(
        cards_frame,
        app.otp_img,
        "OTP Settings",
        ["Account:", masked_email],
        "Edit Email Address",
        app.show_change_OTP_step1_voice_auth_screen
    )

def show_profile_screen(app, event=None):
    """Displays a read-only User Profile screen with profile icon and details."""
    ui_helpers.update_nav_selection(app, "profile")

    LIGHT_CARD_BG = "#AD567C"
    INFO_CARD_BG = "#8D3B63"
    INFO_CARD_TEXT = "#ffffff"

    user = app.currently_logged_in_user
    if not user:
        # Not logged in case
        card = ui_helpers.create_main_card(app, width=600, height=300)
        card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
        tk.Label(
            card,
            text="Please log in to view your profile.",
            font=app.font_large,
            fg=config.TEXT_COLOR,
            bg=LIGHT_CARD_BG,
            wraplength=400
        ).pack(expand=True)
        return

    # --- Main Profile Card ---
    card = ui_helpers.create_main_card(app, width=820, height=480)
    card.config(bg=LIGHT_CARD_BG, relief="flat", bd=0, highlightthickness=0)

    content_frame = tk.Frame(card, bg=LIGHT_CARD_BG)
    content_frame.pack(expand=True, fill="both", padx=30, pady=20)

    # --- Profile Header with Icon ---
    header_frame = tk.Frame(content_frame, bg=LIGHT_CARD_BG)
    header_frame.pack(anchor="center", pady=(10, 25))

    # Use app.profile_img (make sure to load an image in your app init)
    tk.Label(header_frame, image=app.profile_img, bg=LIGHT_CARD_BG).pack(side="top", pady=10)
    tk.Label(
        header_frame, 
        text=f"{user.get('username', 'User')}", 
        font=app.font_large, 
        fg=config.TEXT_COLOR, 
        bg=LIGHT_CARD_BG
    ).pack(side="top")

    # --- Info Card ---
    info_card = tk.Frame(content_frame, bg=INFO_CARD_BG, bd=0, relief="flat")
    info_card.pack(fill="x", padx=40, pady=20)

    body_font = font.Font(family=config.FONT_FAMILY, size=12)

    # User Info (read-only)
    user_info = {
        "Full Name": user.get("full_name", "N/A"),
        "Email": user.get("email", "N/A"),
        "Voice Biometrics": "Enrolled" if user.get("voiceprint_path") else "Not Enrolled",
        "2FA Enabled": "Yes" if user.get("2fa_enabled") else "No"
    }

    for i, (label, value) in enumerate(user_info.items()):
        row = tk.Frame(info_card, bg=INFO_CARD_BG)
        row.pack(anchor="w", pady=6, padx=20, fill="x")

        tk.Label(row, text=f"{label}:", font=app.font_medium_bold, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG).pack(side="left")
        tk.Label(row, text=f" {value}", font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, wraplength=600, justify="left").pack(side="left")


def show_about_screen(app, event=None):
    """Displays the About Us screen with an icon + modern card design."""
    ui_helpers.update_nav_selection(app, None)

    LIGHT_CARD_BG = "#AD567C"
    INFO_CARD_BG = "#8D3B63"
    INFO_CARD_TEXT = "#ffffff"

    card = ui_helpers.create_main_card(app, width=820, height=480)
    card.config(bg=LIGHT_CARD_BG, relief="flat", bd=0, highlightthickness=0)

    content_frame = tk.Frame(card, bg=LIGHT_CARD_BG)
    content_frame.pack(expand=True, pady=20, padx=30, fill="both")

    # --- Title Row with Icon ---
    title_frame = tk.Frame(content_frame, bg=LIGHT_CARD_BG)
    title_frame.pack(anchor="w", pady=(0, 20))

    icon_font = font.Font(family=config.FONT_FAMILY, size=24, weight="bold")
    title_font = font.Font(family=config.FONT_FAMILY, size=22, weight="bold")

    tk.Label(title_frame, text="ℹ️", font=icon_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG).pack(side="left", padx=(0, 10))
    tk.Label(title_frame, text="About Us", font=title_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG).pack(side="left")

    # --- About Text Card ---
    about_card = tk.Frame(content_frame, bg=INFO_CARD_BG, bd=0, relief="flat")
    about_card.pack(pady=(0, 25), fill="x")

    body_font = font.Font(family=config.FONT_FAMILY, size=12)
    about_text = (
        "KeyVox is a plug-and-play hardware authentication token that uses "
        "your unique voice as a robust and secure second factor of authentication (2FA), "
        "powered by advanced LSTM neural networks.\n\n"
        "The key is designed to work with multi-protocol systems such as "
        "FIDO U2F, OATH TOTP, and challenge-response systems."
    )
    tk.Label(
        about_card, text=about_text,
        font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG,
        justify="left", wraplength=720
    ).pack(padx=20, pady=20, anchor="w")

    # --- Subtitle + Bullets ---
    subtitle_font = font.Font(family=config.FONT_FAMILY, size=16, weight="bold")
    tk.Label(
        content_frame, text="How Voice Authentication Works",
        font=subtitle_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG
    ).pack(anchor="w", pady=(0, 15))

    bullets = [
        "Analyze and learn the unique patterns in your voice.",
        "Match live voice input against your stored encrypted voiceprint.",
        "Authenticate only if the match is within the secure threshold."
    ]
    for bullet in bullets:
        tk.Label(
            content_frame, text=f"• {bullet}",
            font=body_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG,
            justify="left", wraplength=700
        ).pack(anchor="w", padx=40, pady=3)

def show_help_screen(app, event=None):
    """Displays the Help/FAQ screen with a modern card design similar to the About Us page."""
    ui_helpers.update_nav_selection(app, None)

    LIGHT_CARD_BG = "#AD567C"
    INFO_CARD_BG = "#8D3B63"
    INFO_CARD_TEXT = "#ffffff"

    # --- Main Card ---
    card = ui_helpers.create_main_card(app, width=820, height=480)
    card.config(bg=LIGHT_CARD_BG, relief="flat", bd=0, highlightthickness=0)

    content_frame = tk.Frame(card, bg=LIGHT_CARD_BG)
    content_frame.pack(expand=True, pady=20, padx=30, fill="both")

    # --- Title Row with Icon ---
    title_frame = tk.Frame(content_frame, bg=LIGHT_CARD_BG)
    title_frame.pack(anchor="w", pady=(0, 20))

    icon_font = font.Font(family=config.FONT_FAMILY, size=24, weight="bold")
    title_font = font.Font(family=config.FONT_FAMILY, size=22, weight="bold")

    tk.Label(title_frame, text="❓", font=icon_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG).pack(side="left", padx=(0, 10))
    tk.Label(title_frame, text="Need Help?", font=title_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG).pack(side="left")

    # --- Info Card: Setup Instructions ---
    setup_card = tk.Frame(content_frame, bg=INFO_CARD_BG, bd=0, relief="flat")
    setup_card.pack(pady=(0, 20), fill="x")

    subtitle_font = font.Font(family=config.FONT_FAMILY, size=16, weight="bold")
    body_font = font.Font(family=config.FONT_FAMILY, size=12)

    tk.Label(
        setup_card, text="Setup Instructions",
        font=subtitle_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG
    ).pack(anchor="w", padx=20, pady=(20, 10))

    setup_steps = [
        "1. Connect your KeyVox device to your computer via USB.",
        "2. Launch the KeyVox App — it can be pre-installed or downloaded from the official source.",
        "3. Begin the voice enrollment process by following the on-screen instructions.",
        "4. Record a short voice phrase 3–5 times in a quiet place to build your secure voiceprint.",
        "5. Configure your preferred authentication protocols (FIDO, OATH, or challenge-response)."
    ]

    for step in setup_steps:
        tk.Label(
            setup_card, text=f"• {step}",
            font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG,
            justify="left", wraplength=720
        ).pack(anchor="w", padx=20, pady=3)

    # --- Info Card: Security Tips ---
    tips_card = tk.Frame(content_frame, bg=INFO_CARD_BG, bd=0, relief="flat")
    tips_card.pack(pady=(0, 25), fill="x")

    tk.Label(
        tips_card, text="Security Tips",
        font=subtitle_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG
    ).pack(anchor="w", padx=20, pady=(20, 10))

    tips = [
        "• Enroll in a quiet environment to ensure clear and accurate voice capture.",
        "• Re-enroll your voice if you experience major changes in your voice tone or quality.",
        "• Avoid sharing your voice recordings or authentication phrases publicly.",
        "• Keep your KeyVox device secure and avoid using it on untrusted computers.",
    ]

    for tip in tips:
        tk.Label(
            tips_card, text=tip,
            font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG,
            justify="left", wraplength=720
        ).pack(anchor="w", padx=20, pady=3)

    # --- Footer Note ---
    footer_font = font.Font(family=config.FONT_FAMILY, size=11, slant="italic")
    tk.Label(
        content_frame,
        text="If you continue experiencing issues, contact KeyVox Support for assistance.",
        font=footer_font, fg=INFO_CARD_TEXT, bg=LIGHT_CARD_BG, justify="left", wraplength=720
    ).pack(anchor="w", pady=(10, 0), padx=20)


