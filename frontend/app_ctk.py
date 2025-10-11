# import customtkinter as ctk
# from PIL import Image, ImageTk
# import os
# import pyaudio
# from tkinter import messagebox

# # Local module imports
# from api_client import APIClient
# import frontend_config as config  
# from ui import ui_helpers, home_screens, login_flow, enrollment_flow, other_screens
# from utils import audio_handler, helpers
# from ui import application_settings

# # Dark Pink Theme Configuration
# DARK_PINK_THEME = {
#     "primary": "#D946A6",          # Vibrant pink
#     "primary_dark": "#BA1B6D",     # Darker pink
#     "primary_light": "#EC4899",    # Lighter pink
#     "background": "#1a1a1a",       # Dark background
#     "secondary_bg": "#2d2d2d",     # Slightly lighter background
#     "tertiary_bg": "#3d3d3d",      # Even lighter for cards
#     "text_primary": "#FFFFFF",     # White text
#     "text_secondary": "#B0B0B0",   # Gray text
#     "accent": "#F472B6",           # Light pink accent
#     "border": "#404040",           # Border color
# }

# class KeyVoxApp:
#     def __init__(self, root):
#         self.root = root
#         self.api = APIClient()
        
#         # --- Set CustomTkinter Theme ---
#         ctk.set_appearance_mode("dark")
#         ctk.set_default_color_theme("dark-blue")  # Base theme
#         self._apply_dark_pink_theme()
        
#         # --- Window and App Configuration ---
#         self.width, self.height = 900, 600
#         self.root.title("Key Vox")
#         self.root.geometry(f"{self.width}x{self.height}")
#         self.root.resizable(False, False)
#         self.root.configure(fg_color=DARK_PINK_THEME["background"])
        
#         if not os.path.exists(config.AUDIO_DIR):
#             os.makedirs(config.AUDIO_DIR)

#         self._load_images()
            
#         # --- State Management ---
#         self.currently_logged_in_user = None
#         self.login_attempt_user = None
#         self.new_enrollment_data = {}
#         self.is_recording = False
#         self.recording_thread = None
#         self.current_phrase_index = 0
#         self.enrollment_phrases = [
#             "My password is my voice", "Authenticate me through speech", 
#             "Nine five two seven echo zebra tree", "Today I confirm my identity using my voice", 
#             "Unlocking access with my voice"
#         ]
#         self.token_id = "f3d4-9a7b-23ce-8e6f"
#         self.just_enrolled = False
#         self.login_flow_state = 'not_started'
#         self.enrollment_state = 'not_started'
#         self.nav_widgets = {}

#         # --- Initialize PyAudio ---
#         self.pyaudio_instance = pyaudio.PyAudio()

#         self._initialize_fonts()
        
#         # --- Build Core UI ---
#         self.main_frame = ctk.CTkFrame(root, fg_color=DARK_PINK_THEME["background"])
#         self.main_frame.pack(fill="both", expand=True)
        
#         # Header frame
#         self.header_frame = ctk.CTkFrame(
#             self.main_frame, 
#             fg_color=DARK_PINK_THEME["secondary_bg"],
#             height=80
#         )
#         self.header_frame.pack(side="top", fill="x", padx=0, pady=0)
        
#         ui_helpers.set_background_image(self)
#         ui_helpers.create_header(self)
        
#         # Content frame
#         self.content_frame = ctk.CTkFrame(
#             self.main_frame,
#             fg_color=DARK_PINK_THEME["background"]
#         )
#         self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
#         self.check_server_and_start()
#         self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

#     def _apply_dark_pink_theme(self):
#         """Apply custom dark pink theme colors to CustomTkinter widgets."""
#         # This sets up the color scheme for all CustomTkinter widgets
#         # Individual widgets can override these defaults
#         pass

#     def _load_images(self):
#         """Loads all necessary images for the application."""
#         try:
#             script_dir = os.path.dirname(os.path.abspath(__file__))

#             # Build absolute paths to the images
#             logo_path = os.path.join(script_dir, "assets", "images", "logo.png")
#             key_path = os.path.join(script_dir, "assets", "images", "key.png")
#             mic_path = os.path.join(script_dir, "assets", "images", "mic.png")
#             otp_path = os.path.join(script_dir, "assets", "images", "otp_settings.png")
#             usb_path = os.path.join(script_dir, "assets", "images", "usb.png")
#             bg_path = os.path.join(script_dir, "assets", "images", "bg.png")
#             eye_open_path = os.path.join(script_dir, "assets", "images", "eyes_open.png")
#             eye_closed_path = os.path.join(script_dir, "assets", "images", "eyes_closed.png")
#             dot_filled_path = os.path.join(script_dir, "assets", "images", "dot_filled.png")
#             dot_empty_path = os.path.join(script_dir, "assets", "images", "dot_empty.png")
#             card_bg_path = os.path.join(script_dir, "assets", "images", "card_background.png")

#             # Load images using absolute paths
#             self.logo_img = ImageTk.PhotoImage(Image.open(logo_path).resize((110, 110), Image.Resampling.LANCZOS))
#             self.key_img = ImageTk.PhotoImage(Image.open(key_path).resize((60, 60), Image.Resampling.LANCZOS))
#             self.mic_img = ImageTk.PhotoImage(Image.open(mic_path).resize((60, 60), Image.Resampling.LANCZOS))
#             self.otp_img = ImageTk.PhotoImage(Image.open(otp_path).resize((60, 60), Image.Resampling.LANCZOS))
#             self.usb_img = ImageTk.PhotoImage(Image.open(usb_path).resize((230, 230), Image.Resampling.LANCZOS))
#             self.bg_img = ImageTk.PhotoImage(Image.open(bg_path).resize((self.width, self.height), Image.Resampling.LANCZOS))
#             self.help_img = ImageTk.PhotoImage(
#                 Image.open("assets/icons/help.png").resize((22, 22), Image.Resampling.LANCZOS)
#             )
#             self.info_img = ImageTk.PhotoImage(
#                 Image.open("assets/icons/info.png").resize((22, 22), Image.Resampling.LANCZOS)
#             )
#             self.eye_open_img = ImageTk.PhotoImage(Image.open(eye_open_path).resize((20, 20), Image.Resampling.LANCZOS))
#             self.eye_closed_img = ImageTk.PhotoImage(Image.open(eye_closed_path).resize((20, 20), Image.Resampling.LANCZOS))
#             self.dot_filled_img = ImageTk.PhotoImage(Image.open(dot_filled_path).resize((12, 12), Image.Resampling.LANCZOS))
#             self.dot_empty_img = ImageTk.PhotoImage(Image.open(dot_empty_path).resize((12, 12), Image.Resampling.LANCZOS))
#             self.profile_img = ImageTk.PhotoImage(
#                 Image.open("assets/images/profile.png").resize((100, 100), Image.Resampling.LANCZOS)
#             )
#             self.card_bg_img = ImageTk.PhotoImage(Image.open(card_bg_path))

#         except FileNotFoundError as e: 
#             messagebox.showerror("Asset Error", f"Image not found: {e.filename}\nPlease ensure 'frontend/assets/images' exists and contains all required images.")
#             self.root.destroy()
#             exit()

#     def _initialize_fonts(self):
#         """Initializes all font styles used in the application."""
#         self.font_nav = (config.FONT_FAMILY, 12)
#         self.font_nav_active = (config.FONT_FAMILY, 12, "bold")
#         self.font_large_bold = (config.FONT_FAMILY, 20, "bold")
#         self.font_large = (config.FONT_FAMILY, 16)
#         self.font_medium_bold = (config.FONT_FAMILY, 14, "bold")
#         self.font_normal = (config.FONT_FAMILY, 10)
#         self.font_small = (config.FONT_FAMILY, 9)

#     def check_server_and_start(self):
#         """Checks backend server status and starts the UI flow."""
#         if not self.api.check_server_status():
#             messagebox.showerror("Connection Error", "Could not connect to the backend server.\nPlease ensure the server is running.")
#             self.root.destroy()
#         else:
#             print("✅ Backend server connected.")
#             self.show_home_screen()
    
#     # --- Screen Navigation & UI Flow Methods ---
#     def show_home_screen(self, event=None): 
#         home_screens.show_home_screen(self)
    
#     def show_applications_screen(self): 
#         other_screens.show_applications_screen(self)
    
#     def show_about_screen(self, event=None): 
#         other_screens.show_about_screen(self)
    
#     def show_help_screen(self, event=None): 
#         other_screens.show_help_screen(self)
    
#     def show_username_entry_screen(self): 
#         login_flow.show_username_entry_screen(self)
    
#     def _handle_username_submit(self): 
#         login_flow.handle_username_submit(self)
    
#     def show_login_voice_auth_screen(self): 
#         login_flow.show_login_voice_auth_screen(self)
    
#     def _handle_login_voice_record(self, event=None): 
#         login_flow.handle_login_voice_record(self, event)
    
#     def _check_password(self): 
#         login_flow.check_password(self)
    
#     def navigate_to_enrollment(self, event=None): 
#         enrollment_flow.navigate_to_enrollment(self)
    
#     def _validate_step1(self): 
#         enrollment_flow.validate_step1(self)
    
#     def show_enrollment_voice_record(self): 
#         enrollment_flow.show_enrollment_voice_record(self)
    
#     def _go_back_phrase(self): 
#         enrollment_flow.go_back_phrase(self)
    
#     def _go_next_phrase(self): 
#         enrollment_flow.go_next_phrase(self)
    
#     def _finish_enrollment(self): 
#         enrollment_flow.finish_enrollment(self)
    
#     def show_change_password_screen(self): 
#         application_settings.show_change_password_screen(self)
    
#     def show_password_screen_voice_entry1(self): 
#         application_settings.show_password_screen_voice_entry1(self)
    
#     def show_otp_settings_screen(self): 
#         application_settings.show_otp_settings_screen(self)
    
#     def show_change_OTP_step1_voice_auth_screen(self): 
#         application_settings.show_change_OTP_step1_voice_auth_screen(self)

#     # --- Utility and Handler Methods ---
#     def toggle_recording(self, event=None): 
#         audio_handler.toggle_recording(self, event)
    
#     def _record_audio_blocking(self, filepath, duration=4): 
#         audio_handler.record_audio_blocking(self, filepath, duration)
    
#     def _mask_email(self, email): 
#         return helpers.mask_email(email)

#     def _on_closing(self):
#         """Handles the window close event gracefully."""
#         self.is_recording = False
#         if self.recording_thread and self.recording_thread.is_alive():
#             self.root.after(100, self._shutdown)
#         else:
#             self._shutdown()

#     def _shutdown(self):
#         """Terminates PyAudio and destroys the root window."""
#         self.pyaudio_instance.terminate()
#         self.root.destroy()

#     def logout_user(self):
#         """Ask confirmation, then log out and return to the welcome screen."""
#         confirm = messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?")
#         if confirm:
#             self.currently_logged_in_user = None
#             home_screens.show_insert_key_screen(self)
        
# if __name__ == "__main__":
#     root = ctk.CTk()
#     app = KeyVoxApp(root)
#     root.mainloop()