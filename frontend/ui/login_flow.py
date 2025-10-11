import tkinter as tk
from tkinter import messagebox
import os
import frontend_config as config
from ui import ui_helpers
from ui import home_screens # <--- CHANGE #1: ADD THIS IMPORT AT THE TOP

def show_username_entry_screen(app):
    """Shows the screen for the user to enter their username."""
    LIGHT_CARD_BG = "#AD567C"

    # --- Clear old widgets ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.login_flow_state = 'username_entry'

    import tkinter.font as tkFont
    font_title = tkFont.Font(family="Poppins", size=16, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_entry = tkFont.Font(family="Poppins", size=11)
    font_small = tkFont.Font(family="Poppins", size=9)
    font_button = tkFont.Font(family="Poppins", size=10)

    # --- Card ---
    card = tk.Frame(app.content_frame, width=420, height=300, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
    card.pack(pady=50)
    card.pack_propagate(False)

    content_wrapper = tk.Frame(card, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
    content_wrapper.pack(expand=True)

    # --- Title & Subtitle (centered) ---
    tk.Label(
        content_wrapper, text="Login", font=font_title,
        fg="white", bg=LIGHT_CARD_BG
    ).pack(pady=(20, 5))

    tk.Label(
        content_wrapper, text="Enter your username to continue",
        font=font_subtitle, fg="white", bg=LIGHT_CARD_BG
    ).pack(pady=(0, 20))

    # --- Username Entry ---
    app.username_entry = tk.Entry(
        content_wrapper, font=font_entry, width=25,
        bg="white", fg="black", relief="flat", bd=0,
        insertbackground="black", justify="center"
    )
    app.username_entry.pack(pady=6, ipady=4)
    app.username_entry.focus_set()

    # --- Error Label ---
    app.username_error_label = tk.Label(
        content_wrapper, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG
    )
    app.username_error_label.pack(pady=(10, 0))

    # --- Continue Button (rounded, centered) ---
    def create_rounded_button(parent, text, command=None, radius=15, width=200, height=40, bg="#F5F5F5", fg="black"):
        wrapper = tk.Frame(parent, bg=LIGHT_CARD_BG)
        wrapper.pack(pady=(20, 10))

        canvas = tk.Canvas(wrapper, width=width, height=height, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0, relief="flat")
        canvas.pack()

        x1, y1, x2, y2 = 2, 2, width-2, height-2

        # Rounded rectangle
        canvas.create_oval(x1, y1, x1 + radius*2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y1, x2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x1, y2 - radius*2, x1 + radius*2, y2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y2 - radius*2, x2, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=bg, outline=bg)

        # Centered text
        btn_text = canvas.create_text(width//2, height//2, text=text, fill=fg, font=font_button)

        def on_click(event):
            if command:
                command()
        canvas.tag_bind(btn_text, "<Button-1>", on_click)
        canvas.bind("<Button-1>", on_click)

        return wrapper

    create_rounded_button(content_wrapper, "Continue", command=app._handle_username_submit)

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
    LIGHT_CARD_BG = "#AD567C"

    # --- Clear old widgets ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.login_flow_state = 'voice_auth'
    username = app.login_attempt_user.get("username", "User")

    # --- Fonts ---
    import tkinter.font as tkFont
    font_title = tkFont.Font(family="Poppins", size=16, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=12)
    font_label = tkFont.Font(family="Poppins", size=11)
    font_small = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=11)

    # --- Centering trick for the whole content ---
    app.content_frame.grid_rowconfigure(0, weight=1)
    app.content_frame.grid_columnconfigure(0, weight=1)

    # --- Main Card (moderate size) ---
    card = tk.Frame(app.content_frame, width=500, height=400, bg=LIGHT_CARD_BG)
    card.grid(row=0, column=0, sticky="nsew")
    card.grid_propagate(False)

    # Grid balance inside card
    for r in range(6):
        card.grid_rowconfigure(r, weight=1)
    card.grid_columnconfigure(0, weight=1)

    # --- Title (extra top margin) ---
    tk.Label(
        card, text=f"Welcome, {username}!", font=font_title,
        fg="white", bg=LIGHT_CARD_BG
    ).grid(row=0, column=0, pady=(40, 10), sticky="n")

    # --- Instruction ---
    tk.Label(
        card, text='Please say: "My voice is my password"',
        font=font_subtitle, fg="#F5C6E0",
        bg=LIGHT_CARD_BG, wraplength=600, justify="center"
    ).grid(row=1, column=0, pady=(1, 10), sticky="n")

    # --- Mic Icon ---
    mic_label = tk.Label(card, image=app.mic_img, bg=LIGHT_CARD_BG, cursor="hand2")
    mic_label.grid(row=2, column=0, pady=(10, 10))
    mic_label.bind("<Button-1>", app._handle_login_voice_record)

    # --- Status Label ---
    app.recording_status_label = tk.Label(
        card, text="Click the mic to authenticate",
        font=font_small, fg="white", bg=LIGHT_CARD_BG
    )
    app.recording_status_label.grid(row=3, column=0, pady=(5, 10))

    # --- Spacer ---
    tk.Label(card, text="", bg=LIGHT_CARD_BG).grid(row=4, column=0)

    # --- Bottom Frame ---
    bf = tk.Frame(card, bg=LIGHT_CARD_BG)
    bf.grid(row=5, column=0, sticky="ew", padx=60, pady=(10, 20))

    tk.Button(
        bf, text="Cancel", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat",
        padx=15, pady=6, command=lambda: home_screens.show_insert_key_screen(app) # <--- CHANGE #2: FIX THE COMMAND
    ).pack(side="right")


def handle_login_voice_record(app, event=None):
    """Handles the recording and API verification for voice login (bypassed to always succeed)."""
    username = app.login_attempt_user.get('username')
    if not username:
        messagebox.showerror("Error", "Username missing.")
        return

    app.recording_status_label.config(text="Recording (4s)...")
    app.root.update_idletasks()
    
    filepath = os.path.join(config.AUDIO_DIR, f"verify_{username}.wav")
    app._record_audio_blocking(filepath, duration=4)
    
    # Simulate verification bypass
    app.recording_status_label.config(text="Verifying...")
    app.root.update_idletasks()
    
    # --- Always accept ---
    messagebox.showinfo("Success", "Voice Authenticated! Please enter your password.")
    show_password_screen(app)

def show_password_screen(app):
    """Shows the final password entry screen with a visibility toggle."""
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

    # --- [NEW] Frame to hold both the Entry and the Eye Icon ---
    entry_frame = tk.Frame(content_wrapper, bg="white")
    entry_frame.pack(pady=10)

    # --- Password Entry ---
    app.password_entry = tk.Entry(
        entry_frame, # Parent is now the new frame
        font=app.font_large,
        fg="black",
        bg="white",
        show="*",
        width=22, # Slightly reduced width to make space for the icon
        relief="flat",
        bd=0,
        justify="center",
        insertbackground="black"
    )
    app.password_entry.pack(side="left", ipady=5, padx=(10, 0))
    app.password_entry.focus_set()

    # --- [NEW] Function to toggle password visibility ---
    def toggle_password_visibility():
        if app.password_entry.cget('show') == '*':
            app.password_entry.config(show='')
            eye_button.config(image=app.eye_closed_img)
        else:
            app.password_entry.config(show='*')
            eye_button.config(image=app.eye_open_img)

    # --- [NEW] The Eye Icon Button ---
    eye_button = tk.Button(
        entry_frame, # Parent is also the new frame
        image=app.eye_open_img,
        bg="white",
        relief="flat",
        bd=0,
        activebackground="white",
        command=toggle_password_visibility,
        cursor="hand2"
    )
    eye_button.pack(side="right", padx=(0, 5))


    # --- Rounded "Confirm Login" Button (Your original function) ---
    def create_rounded_button(parent, text, command=None, radius=15, width=200, height=40, bg="#F5F5F5", fg="black"):
        wrapper = tk.Frame(parent, bg=LIGHT_CARD_BG)
        wrapper.pack(pady=(20, 15))

        canvas = tk.Canvas(wrapper, width=width, height=height, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0, relief="flat")
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

    # The button now correctly calls your original _check_password function
    create_rounded_button(content_wrapper, "Confirm Login", command=app._check_password)

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