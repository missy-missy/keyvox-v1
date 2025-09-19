import tkinter as tk
import frontend_config as config

def set_background_image(app):
    """Sets the background image on the main canvas."""
    # This function assumes 'app.bg_img' has already been loaded in the main app class.
    # It places the image at coordinate (0, 0) with the anchor at the top-left corner.
    app.canvas.create_image(0, 0, anchor="nw", image=app.bg_img)

def create_header(app):
    """Creates the top header with logo, navigation, and status icons."""
    nav_y_center, line_y, side_padding = 50, 70, 40
    app.canvas.create_image(side_padding, line_y / 1.2, anchor="w", image=app.logo_img, tags="logo")
    
    current_x = app.width - side_padding
    info_tag = "info_icon"
    info_rect_id = app.canvas.create_rectangle(current_x - 22, nav_y_center - 11, current_x, nav_y_center + 11, fill=config.PLACEHOLDER_COLOR, outline=config.PLACEHOLDER_COLOR, tags=info_tag)
    app.canvas.create_text(current_x - 11, nav_y_center, text="i", font=("Arial", 12, "bold"), fill=config.TEXT_COLOR, tags=info_tag)
    app.canvas.tag_bind(info_tag, "<Button-1>", app.show_about_screen)
    app.canvas.tag_bind(info_tag, "<Enter>", lambda e: app.canvas.config(cursor="hand2"))
    app.canvas.tag_bind(info_tag, "<Leave>", lambda e: app.canvas.config(cursor=""))

    line_x1 = app.canvas.bbox(info_rect_id)[2]
    current_x -= 32 
    help_tag = "help_icon"
    app.canvas.create_rectangle(current_x - 22, nav_y_center - 11, current_x, nav_y_center + 11, fill=config.PLACEHOLDER_COLOR, outline=config.PLACEHOLDER_COLOR, tags=help_tag)
    app.canvas.create_text(current_x - 11, nav_y_center, text="?", font=("Arial", 12, "bold"), fill=config.TEXT_COLOR, tags=help_tag)
    app.canvas.tag_bind(help_tag, "<Button-1>", app.show_help_screen)
    app.canvas.tag_bind(help_tag, "<Enter>", lambda e: app.canvas.config(cursor="hand2"))
    app.canvas.tag_bind(help_tag, "<Leave>", lambda e: app.canvas.config(cursor=""))

    current_x -= 32
    app.canvas.create_oval(current_x - 12, nav_y_center - 6, current_x, nav_y_center + 6, fill="#2ecc71", outline="")
    current_x -= 17
    app.canvas.create_text(current_x, nav_y_center, text="status:", font=app.font_small, fill=config.TEXT_COLOR, anchor="e")

    start_x = 180
    nav_map = {"home": app.show_home_screen, "Applications": app.show_applications_screen, "Enrollment": app.navigate_to_enrollment}
    first_tab_bbox = None
    for key, command in nav_map.items():
        text, tag = key.capitalize(), f"nav_{key}"
        text_id = app.canvas.create_text(start_x, nav_y_center, text=text, font=app.font_nav, fill=config.TEXT_COLOR, anchor="w", tags=tag)
        app.canvas.tag_bind(tag, "<Button-1>", lambda e, cmd=command: cmd())
        app.canvas.tag_bind(tag, "<Enter>", lambda e: app.canvas.config(cursor="hand2"))
        app.canvas.tag_bind(tag, "<Leave>", lambda e: app.canvas.config(cursor=""))
        bbox = app.canvas.bbox(text_id)
        if first_tab_bbox is None: first_tab_bbox = bbox
        underline_id = app.canvas.create_line(bbox[0], line_y, bbox[2], line_y, fill=config.TEXT_COLOR, width=3, state='hidden')
        app.nav_widgets[key.lower()] = {'text_id': text_id, 'underline_id': underline_id}
        start_x = bbox[2] + 45
        
    if first_tab_bbox:
        line_x0 = first_tab_bbox[0]
        app.canvas.create_line(line_x0, line_y, line_x1, line_y, fill=config.TEXT_COLOR, width=1)


def update_nav_selection(app, key):
    """Updates the visual selection indicator for the navigation tabs."""
    if key: key = key.lower()
    for k, w in app.nav_widgets.items():
        app.canvas.itemconfig(w['text_id'], font=app.font_nav)
        app.canvas.itemconfig(w['underline_id'], state='hidden')
    if key and key in app.nav_widgets:
        w = app.nav_widgets[key]
        app.canvas.itemconfig(w['text_id'], font=app.font_nav_active)
        app.canvas.itemconfig(w['underline_id'], state='normal')

def clear_content_frame(app):
    """Destroys all widgets in the main content frame."""
    for w in app.content_frame.winfo_children():
        w.destroy()
    app.content_frame.config(bg="#7c2e50", bd=0)

def create_main_card(app, width=600, height=400):
    """Clears the content frame and creates a new main card to hold content."""
    clear_content_frame(app)
    card = tk.Frame(app.content_frame, bg=config.CARD_BG_COLOR, relief="solid", bd=1, width=width, height=height)
    card.pack(pady=20)
    card.pack_propagate(False)
    return card