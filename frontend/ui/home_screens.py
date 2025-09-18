import tkinter as tk
from .. import config
from . import ui_helpers

def show_home_screen(app, event=None):
    """Acts as a router for the home screen based on login or enrollment state."""
    ui_helpers.update_nav_selection(app, "home")

    if app.currently_logged_in_user:
        show_logged_in_screen(app)
        return

    if app.just_enrolled:
        app.just_enrolled = False
        app.login_attempt_user = {"username": app.just_enrolled_username}
        app.show_login_voice_auth_screen()
        return
        
    show_insert_key_screen(app)

def show_insert_key_screen(app):
    """The initial welcome screen prompting the user to start the login process."""
    app.login_flow_state = 'not_started'
    app.currently_logged_in_user = None
    app.login_attempt_user = None
    card = ui_helpers.create_main_card(app, width=500, height=350)
    
    content_wrapper = tk.Frame(card, bg=config.CARD_BG_COLOR)
    content_wrapper.pack(expand=True)
    tk.Label(content_wrapper, image=app.key_img, bg=config.CARD_BG_COLOR).pack(pady=(20, 10))
    tk.Label(content_wrapper, text="Welcome to Key Vox", font=app.font_large, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=10)
    tk.Button(content_wrapper, text="Begin Login", font=app.font_normal, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, command=app.show_username_entry_screen, padx=20, pady=5, relief="flat").pack(pady=20)
    tk.Label(content_wrapper, text="No account? Go to the Enrollment tab.", font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=10)

def show_logged_in_screen(app):
    """Displays the screen for a successfully logged-in user."""
    card = ui_helpers.create_main_card(app, width=500, height=420)
    
    content_wrapper = tk.Frame(card, bg=config.CARD_BG_COLOR)
    content_wrapper.pack(expand=True, pady=20)

    tk.Label(content_wrapper, image=app.usb_img, bg=config.CARD_BG_COLOR).pack(pady=(0, 20))
    tk.Label(content_wrapper, text="Token ID:", font=app.font_normal, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack()
    tk.Label(content_wrapper, text=app.token_id, font=app.font_large, fg=config.TEXT_COLOR, bg=config.CARD_BG_COLOR).pack(pady=(5, 25))
    tk.Button(
        content_wrapper, 
        text="Manage Applications", 
        font=app.font_normal, 
        bg=config.BUTTON_LIGHT_COLOR, 
        fg=config.BUTTON_LIGHT_TEXT_COLOR, 
        relief="flat",
        padx=20, 
        pady=5, 
        command=app.show_applications_screen
    ).pack()

def logout(app):
    """Logs the user out and returns to the initial welcome screen."""
    app.currently_logged_in_user = None
    show_insert_key_screen(app)