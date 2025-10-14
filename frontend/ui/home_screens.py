import tkinter as tk
import frontend_config as config
from . import ui_helpers
from PIL import Image, ImageTk
import tkinter.font as tkFont

def show_home_screen(app, event=None):
    """Acts as a router for the home screen based on login state."""
    ui_helpers.update_nav_selection(app, "home")

    if app.currently_logged_in_user:
        # If a user is logged in, show their main screen
        show_logged_in_screen(app)
    else:
        # If no user is logged in, show the initial screen to start the process
        show_insert_key_screen(app)

def show_insert_key_screen(app):
    """A simple, modern welcome screen with a lighter card and no excessive space."""
    # app.login_flow_state = 'not_started'
    # app.currently_logged_in_user = None
    # app.login_attempt_user = None

    LIGHT_CARD_BG = "#AD567C" 

    card = ui_helpers.create_main_card(app, width=450, height=350)
    card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)

    content_wrapper = tk.Frame(card, bg=LIGHT_CARD_BG, bd=0, highlightthickness=-0)
    content_wrapper.pack(expand=True)

    tk.Label(
        content_wrapper,
        image=app.lock_img,
        bg=LIGHT_CARD_BG
    ).pack(pady=(8, 10))

    tk.Label(
        content_wrapper,
        text="Welcome to KeyVox",
        font=app.font_large,
        fg=config.TEXT_COLOR,
        bg=LIGHT_CARD_BG
    ).pack(pady=(0, 14))

    # ---- Rounded "Begin Login" Button ----
    def create_rounded_button(parent, text, command=None, radius=15, width=200, height=40, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR):
        wrapper = tk.Frame(parent, bg=LIGHT_CARD_BG)  # para align siya sa iba
        wrapper.pack(pady=(0, 16))

        canvas = tk.Canvas(wrapper, width=width, height=height, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0, relief="flat")
        canvas.pack()

        x1, y1, x2, y2 = 2, 2, width-2, height-2

        # Rounded rectangle parts
        canvas.create_oval(x1, y1, x1 + radius*2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y1, x2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x1, y2 - radius*2, x1 + radius*2, y2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y2 - radius*2, x2, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=bg, outline=bg)

        # Centered text
        btn_text = canvas.create_text(width//2, height//2, text=text, fill=fg, font=app.font_normal)

        # Click binding
        def on_click(event):
            if command:
                command()
        canvas.tag_bind(btn_text, "<Button-1>", on_click)
        canvas.bind("<Button-1>", on_click)

        return wrapper

    create_rounded_button(content_wrapper, "Begin Login", command=app.show_username_entry_screen)


    tk.Label(
        content_wrapper,
        text="No account? Go to the Enrollment tab.",
        font=app.font_normal,
        fg="#D9D9D9",  # Lighter info text
        bg=LIGHT_CARD_BG
    ).pack(pady=(0, 0))

# def show_logged_in_screen(app):
#     """Displays the screen for a successfully logged-in user."""
#     LIGHT_CARD_BG = "#AD567C"

#     # --- Card ---
#     card = ui_helpers.create_main_card(app, width=420, height=420)
#     card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)

#     content_wrapper = tk.Frame(card, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
#     content_wrapper.pack(expand=True, pady=20)

#     # --- Title ---
#     tk.Label(
#         content_wrapper,
#         text="Security Token Detected",
#         font=app.font_large,
#         fg="white",
#         bg=LIGHT_CARD_BG
#     ).pack(pady=(10, 15))


#     # --- Resize USB Logo ---
#     try:
#         usb_img_resized = Image.open("assets/images/usb.png").resize((100, 100), Image.Resampling.LANCZOS)
#         app.usb_img_small = ImageTk.PhotoImage(usb_img_resized)
#         tk.Label(
#             content_wrapper,
#             image=app.usb_img_small,
#             bg=LIGHT_CARD_BG
#         ).pack(pady=(0, 15))
#     except Exception as e:
#         print(f"DEBUG: Could not resize usb.png: {e}")
#         tk.Label(content_wrapper, text="[USB Icon]", bg=LIGHT_CARD_BG, fg="white").pack(pady=(0, 15))

#     # --- Token Info ---
#     tk.Label(
#         content_wrapper,
#         text="Token ID:",
#         font=app.font_normal,
#         fg="white",
#         bg=LIGHT_CARD_BG
#     ).pack()

#     tk.Label(
#         content_wrapper,
#         text=app.token_id,
#         font=app.font_large,
#         fg="white",
#         bg=LIGHT_CARD_BG
#     ).pack(pady=(5, 20))

#     # --- Rounded "Manage Applications" Button ---
#     def create_rounded_button(parent, text, command=None, radius=15, width=220, height=42, bg="#F5F5F5", fg="black"):
#         wrapper = tk.Frame(parent, bg=LIGHT_CARD_BG)
#         wrapper.pack(pady=(0, 10))

#         canvas = tk.Canvas(wrapper, width=width, height=height, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0, relief="flat")
#         canvas.pack()

#         x1, y1, x2, y2 = 2, 2, width-2, height-2

#         # Rounded rectangle
#         canvas.create_oval(x1, y1, x1 + radius*2, y1 + radius*2, fill=bg, outline=bg)
#         canvas.create_oval(x2 - radius*2, y1, x2, y1 + radius*2, fill=bg, outline=bg)
#         canvas.create_oval(x1, y2 - radius*2, x1 + radius*2, y2, fill=bg, outline=bg)
#         canvas.create_oval(x2 - radius*2, y2 - radius*2, x2, y2, fill=bg, outline=bg)
#         canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=bg, outline=bg)
#         canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=bg, outline=bg)

#         # Centered text
#         btn_text = canvas.create_text(width//2, height//2, text=text, fill=fg, font=app.font_normal)

#         def on_click(event):
#             if command:
#                 command()
#         canvas.tag_bind(btn_text, "<Button-1>", on_click)
#         canvas.bind("<Button-1>", on_click)

#         return wrapper

#     create_rounded_button(content_wrapper, "Log Out", command=app.logout_user, bg="#950D58", fg="white")

def create_main_card(app, width, height):
    """Creates a centered frame within the app's content_frame."""
    card = tk.Frame(app.content_frame, width=width, height=height)
    card.pack_propagate(False) # Prevent card from shrinking to fit content
    card.pack(expand=True)
    return card

def create_main_card(app, width, height):
    """Creates a centered frame within the app's content_frame."""
    card = tk.Frame(app.content_frame, width=width, height=height)
    card.pack_propagate(False)
    card.pack(expand=True)
    return card

def show_logged_in_screen(app):
    """Displays a modern, success-themed screen for a logged-in user."""
    # --- 1. Theme and Styling (as requested) ---
    COLOR_BACKGROUND = "#AD567C"
    COLOR_CARD_BG = "#AD567C"
    COLOR_TEXT = "#E0E0E0"
    COLOR_SUCCESS = "#ffffff"
    COLOR_BUTTON_BG = "#950D58"

    # --- Font Sizes ---
    FONT_FAMILY = "Segoe UI"
    font_title = tkFont.Font(family=FONT_FAMILY, size=16, weight="bold")
    font_subtitle = tkFont.Font(family=FONT_FAMILY, size=10)
    font_token_label = tkFont.Font(family=FONT_FAMILY, size=9)
    font_token_id = tkFont.Font(family=FONT_FAMILY, size=11, weight="bold")
    font_button = tkFont.Font(family=FONT_FAMILY, size=10, weight="bold")
    
    # --- 2. Setup ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.content_frame.configure(bg=COLOR_BACKGROUND)

    # --- 3. Main Card & Content Wrapper (Height Reduced) ---
    card = create_main_card(app, width=360, height=370) # <-- Reduced height from 420
    card.config(bg=COLOR_CARD_BG, bd=0, highlightthickness=0)

    content_wrapper = tk.Frame(card, bg=COLOR_CARD_BG)
    content_wrapper.pack(expand=True, fill="both", padx=25, pady=20)

    # --- 4. Screen Content ---

    # Title
    tk.Label(
        content_wrapper, text="Security Token Detected", font=font_title, fg=COLOR_TEXT, bg=COLOR_CARD_BG
    ).pack(pady=(5, 8))
    
    # USB Icon
    tk.Label(
        content_wrapper,
        image=app.usb_img_4,
        bg=COLOR_CARD_BG
    ).pack(pady=(5, 8))
    
    # Subtitle
    tk.Label(
        content_wrapper,
        text="Your security token has been verified.",
        font=font_subtitle,
        fg=COLOR_TEXT,
        bg=COLOR_CARD_BG,
        wraplength=280
    ).pack(pady=(0, 20))
    
    # Separator
    separator = tk.Frame(content_wrapper, height=1, bg="#FFFFFF")
    separator.pack(fill="x", pady=8)

    # Token Info Frame
    token_frame = tk.Frame(content_wrapper, bg=COLOR_CARD_BG)
    token_frame.pack(pady=8)

    tk.Label(
        token_frame, text="TOKEN ID", font=font_token_label, fg=COLOR_TEXT, bg=COLOR_CARD_BG
    ).pack()
    
    # Token ID
    tk.Label(
        token_frame, text=app.token_id, font=font_token_id, fg=COLOR_SUCCESS, bg=COLOR_CARD_BG
    ).pack(pady=4)
    
    # --- The expanding spacer has been removed ---

    # Log Out Button
    logout_button = tk.Button(
        content_wrapper,
        text="Log Out",
        font=font_button,
        bg=COLOR_BUTTON_BG,
        fg=COLOR_TEXT,
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
        activebackground="#950D58",
        activeforeground=COLOR_TEXT,
        pady=8,
        command=app.logout_user
    )
    # This padding now creates a smaller, fixed space above the button
    logout_button.pack(fill="x", side="bottom", pady=(15, 0))

def logout(app):
    """Logs the user out and returns to the initial welcome screen."""
    app.currently_logged_in_user = None
    show_insert_key_screen(app)