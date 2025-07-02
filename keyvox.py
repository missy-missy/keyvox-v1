import tkinter as tk
from tkinter import font, messagebox
import time
import os
import wave
import pyaudio
import threading
import random
import json
from PIL import Image, ImageTk

# --- UI Configuration
GRADIENT_TOP_COLOR = "#5e213f"; GRADIENT_BOTTOM_COLOR = "#983a62"; CARD_BG_COLOR = "#6a2f4b"
TEXT_COLOR = "#ffffff"; BUTTON_COLOR = "#c8356e"; BUTTON_LIGHT_COLOR = "#f0f0f0"
BUTTON_LIGHT_TEXT_COLOR = "#333333"; ERROR_COLOR = "#ff6b6b"; FONT_FAMILY = "Segoe UI"; PLACEHOLDER_COLOR = "#333333"

# --- App Config ---
AUDIO_DIR = "enrollment_audio"; DATA_FILE = "keyvox_data.json"
CHUNK = 1024; FORMAT = pyaudio.paInt16; CHANNELS = 1; RATE = 44100

class KeyVoxApp:
    def __init__(self, root):
        self.root = root
        self.width, self.height = 900, 600
        self.root.title("Key Vox"); self.root.geometry(f"{self.width}x{self.height}"); self.root.resizable(False, False)
        if not os.path.exists(AUDIO_DIR): os.makedirs(AUDIO_DIR)

        try:
           
            self.logo_img = ImageTk.PhotoImage(Image.open("images/logo.png").resize((110, 110), Image.Resampling.LANCZOS))
            self.key_img = ImageTk.PhotoImage(Image.open("images/key.png").resize((60, 60), Image.Resampling.LANCZOS))
            self.mic_img = ImageTk.PhotoImage(Image.open("images/mic.png").resize((60, 60), Image.Resampling.LANCZOS))
            self.otp_img = ImageTk.PhotoImage(Image.open("images/otp_settings.png").resize((60, 60), Image.Resampling.LANCZOS))
            self.usb_img = ImageTk.PhotoImage(Image.open("images/usb.png").resize((230, 230), Image.Resampling.LANCZOS))
        except FileNotFoundError as e:
            messagebox.showerror("Error", f"Image not found: {e.filename}\nPlease make sure 'images' folder and all PNG files exist.")
            root.destroy()
            return
            
        self.enrolled_users = []
        self.currently_logged_in_user = None
        self.login_attempt_user = None 
        self._load_data_from_file()

        self.token_id = "f3d4-9a7b-23ce-8e6f"
        self.just_enrolled = False
        self.login_flow_state = 'not_started' 
        self.enrollment_state = 'not_started'; self.simulated_enrollment_otp = None
        self.password_reset_otp = None; self.current_phrase_index = 0; self.is_recording = False
        self.recording_thread = None; self.pyaudio_instance = pyaudio.PyAudio()
        self.enrollment_phrases = ["My password is my voice", "Authenticate me through speech", "Nine five two seven echo zebra tree", "Today I confirm my identity using my voice", "Unlocking access with my voice"]
        self.nav_widgets = {}

        self.font_nav=font.Font(family=FONT_FAMILY,size=12); self.font_nav_active=font.Font(family=FONT_FAMILY,size=12,weight="bold"); self.font_large_bold=font.Font(family=FONT_FAMILY,size=20,weight="bold"); self.font_large=font.Font(family=FONT_FAMILY,size=16); self.font_medium_bold=font.Font(family=FONT_FAMILY,size=14,weight="bold"); self.font_normal=font.Font(family=FONT_FAMILY,size=10); self.font_small=font.Font(family=FONT_FAMILY,size=9)
        
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, highlightthickness=0); self.canvas.pack(fill="both", expand=True); self._create_gradient(GRADIENT_TOP_COLOR, GRADIENT_BOTTOM_COLOR); self._create_header()
        self.content_frame = tk.Frame(self.canvas, bg="#7c2e50"); self.canvas.create_window(self.width/2, self.height/2 + 60, window=self.content_frame, anchor="center")
        self.show_home_screen()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    # --- DATA & UI HELPERS ---
    def _load_data_from_file(self):
        try:
            with open(DATA_FILE, 'r') as f: data = json.load(f); self.enrolled_users = data.get('enrolled_users', [])
        except (FileNotFoundError, json.JSONDecodeError):
            self.enrolled_users = [{"full_name": "Default User", "username": "admin", "password": "password123", "voice_status": "Enrolled", "email": "admin@keyvox.com"}]
            self._save_data_to_file()
        print(f"Data loaded: {len(self.enrolled_users)} user(s) found.")

    def _save_data_to_file(self):
        with open(DATA_FILE, 'w') as f: json.dump({'enrolled_users': self.enrolled_users}, f, indent=4)
        print("Data saved to file.")

    def _create_gradient(self, c1, c2):
        r1,g1,b1=self.root.winfo_rgb(c1);r2,g2,b2=self.root.winfo_rgb(c2);r,g,b=(r2-r1)/self.height,(g2-g1)/self.height,(b2-b1)/self.height
        for i in range(self.height):self.canvas.create_line(0,i,self.width,i,fill=f"#{int(r1+r*i):04x}{int(g1+g*i):04x}{int(b1+b*i):04x}")
    
    def _create_header(self):
        # --- Vertical Alignment & Padding ---
       
        nav_y_center = 50  
        line_y = nav_y_center + 20   
        side_padding = 40 

        # 1. Logo 
        self.canvas.create_image(side_padding, line_y / 1.2, anchor="w", image=self.logo_img, tags="logo")
        
        
        # --- Status Icons (Right side) ---
        current_x = self.width - side_padding
        
        # Info Icon ('i')
        info_tag = "info_icon"
        info_rect_id = self.canvas.create_rectangle(current_x - 22, nav_y_center - 11, current_x, nav_y_center + 11, fill=PLACEHOLDER_COLOR, outline=PLACEHOLDER_COLOR, tags=info_tag)
        self.canvas.create_text(current_x - 11, nav_y_center, text="i", font=("Arial", 12, "bold"), fill=TEXT_COLOR, tags=info_tag)
        self.canvas.tag_bind(info_tag, "<Button-1>", self.show_about_screen)
        self.canvas.tag_bind(info_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(info_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))
        line_x1 = self.canvas.bbox(info_rect_id)[2] 
        current_x -= (22 + 10)

        # Help Icon ('?')
        help_tag = "help_icon"
        self.canvas.create_rectangle(current_x - 22, nav_y_center - 11, current_x, nav_y_center + 11, fill=PLACEHOLDER_COLOR, outline=PLACEHOLDER_COLOR, tags=help_tag)
        self.canvas.create_text(current_x - 11, nav_y_center, text="?", font=("Arial", 12, "bold"), fill=TEXT_COLOR, tags=help_tag)
        self.canvas.tag_bind(help_tag, "<Button-1>", self.show_help_screen)
        self.canvas.tag_bind(help_tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(help_tag, "<Leave>", lambda e: self.canvas.config(cursor=""))
        current_x -= (22 + 10)

        # Status Dot
        self.canvas.create_oval(current_x - 12, nav_y_center - 6, current_x, nav_y_center + 6, fill="#2ecc71", outline="")
        current_x -= (12 + 5)

        # Status Text
        self.canvas.create_text(current_x, nav_y_center, text="status:", font=self.font_small, fill=TEXT_COLOR, anchor="e")

        # --- Navigation Tabs (Left side) ---
        start_x = 180 
        nav_map = {"home": self.show_home_screen, "Applications": self.show_applications_screen, "Enrollment": self.navigate_to_enrollment}
        
        first_tab_bbox = None
        for key, command in nav_map.items():
            text = key.capitalize()
            tag = f"nav_{key}"
            
            text_id = self.canvas.create_text(start_x, nav_y_center, text=text, font=self.font_nav, fill=TEXT_COLOR, anchor="w", tags=tag)
            
            self.canvas.tag_bind(tag, "<Button-1>", lambda e, cmd=command: cmd())
            self.canvas.tag_bind(tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: self.canvas.config(cursor=""))
            
            bbox = self.canvas.bbox(text_id)
            if first_tab_bbox is None:
                first_tab_bbox = bbox
                
            underline_id = self.canvas.create_line(bbox[0], line_y, bbox[2], line_y, fill=TEXT_COLOR, width=3, state='hidden')
            
            
            self.nav_widgets[key.lower()] = {'text_id': text_id, 'underline_id': underline_id}
            
            start_x = bbox[2] + 45

        # --- Bottom Divider Line ---
        if first_tab_bbox:
            line_x0 = first_tab_bbox[0] # Get left edge of the "Home" tab
            self.canvas.create_line(line_x0, line_y, line_x1, line_y, fill=TEXT_COLOR, width=1)


    def _update_nav_selection(self, key):
        if key:
            key = key.lower()
        
       
        for k, w in self.nav_widgets.items():
            self.canvas.itemconfig(w['text_id'], font=self.font_nav)
            self.canvas.itemconfig(w['underline_id'], state='hidden')
        
        # Activate the selected nav item
        if key and key in self.nav_widgets:
            w = self.nav_widgets[key]
            self.canvas.itemconfig(w['text_id'], font=self.font_nav_active)
            self.canvas.itemconfig(w['underline_id'], state='normal')
            
    def _clear_content_frame(self):
        for w in self.content_frame.winfo_children(): w.destroy()
        self.content_frame.config(bg="#7c2e50", bd=0)

    def _create_main_card(self, width=600, height=400):
        self._clear_content_frame()
        card = tk.Frame(self.content_frame, bg=CARD_BG_COLOR, relief="solid", bd=1, width=width, height=height)
        card.pack(pady=20)
        # This is critical. It stops the parent frame from shrinking to fit its contents.
        card.pack_propagate(False) 
        return card

    # --- HOME, INFO & LOGIN FLOW ---
    def show_home_screen(self, event=None):
        self._update_nav_selection("home")
        if self.currently_logged_in_user:
            self.show_logged_in_screen()
            return
        if self.just_enrolled: 
            self.just_enrolled = False
            self.show_login_voice_auth_screen()
            return
        resume_map = {'not_started': self.show_insert_key_screen, 'voice_auth': self.show_login_voice_auth_screen, 'password_entry': self.show_password_screen, 'password_reset_email': self.show_forgot_password_email_screen, 'password_reset_new_pw': self.show_forgot_password_new_pw_screen}
        if self.login_flow_state in resume_map: resume_map[self.login_flow_state]()
        else: self.show_insert_key_screen()
            
    def show_about_screen(self, event=None):
        self._update_nav_selection(None) 
        INFO_CARD_BG = "#e9e3e6"
        INFO_CARD_TEXT = "#3b3b3b"
        
        card = self._create_main_card(width=820, height=480)
        card.config(bg=INFO_CARD_BG, relief="flat", bd=0, highlightthickness=0)
        
        content_frame = tk.Frame(card, bg=INFO_CARD_BG)
       
        content_frame.pack(expand=True)
        
        title_font = font.Font(family=FONT_FAMILY, size=22, weight="bold")
        tk.Label(content_frame, text="About Us", font=title_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left").pack(anchor="w", pady=(0, 20))
        
        body_font = font.Font(family=FONT_FAMILY, size=12)
        about_text = "KeyVox is a new plug-and-play hardware authentication token that uses your unique voice as a robust and secure second factor of authentication (2FA), powered by advanced LSTM neural networks. The key is designed to work with multi-protocol systems such as FIDO U2F, OATH TOTP, challenge response system."
        tk.Label(content_frame, text=about_text, font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left", wraplength=720).pack(anchor="w", pady=(0, 30))
        
        subtitle_font = font.Font(family=FONT_FAMILY, size=16, weight="bold")
        tk.Label(content_frame, text="How Voice Authentication Works", font=subtitle_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left").pack(anchor="w", pady=(0, 15))
        
        tk.Label(content_frame, text="KeyVox uses LSTM-based voice biometrics to:", font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left").pack(anchor="w", pady=(0, 10))
        
        bullets = [
            "Analyze and learn the unique patterns in your voice.",
            "Match live voice input against your stored encrypted voiceprint.",
            "Authenticate only if the match is within the secure threshold."
        ]
        
        for bullet in bullets:
            tk.Label(content_frame, text=f"  •  {bullet}", font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left", wraplength=700).pack(anchor="w", pady=2)

    def show_help_screen(self, event=None):
        self._update_nav_selection(None)
       
        INFO_CARD_BG = "#e9e3e6"
        INFO_CARD_TEXT = "#3b3b3b"

        card = self._create_main_card(width=820, height=480)
        card.config(bg=INFO_CARD_BG, relief="flat", bd=0, highlightthickness=0)
        
        content_frame = tk.Frame(card, bg=INFO_CARD_BG)
        
        content_frame.pack(expand=True)
        
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)

        title_font = font.Font(family=FONT_FAMILY, size=22, weight="bold")
        tk.Label(content_frame, text="Need Help?", font=title_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 25))

        left_frame = tk.Frame(content_frame, bg=INFO_CARD_BG)
        left_frame.grid(row=1, column=0, sticky="nw", padx=(0, 20))
        
        subtitle_font = font.Font(family=FONT_FAMILY, size=16, weight="bold")
        tk.Label(left_frame, text="Setup Instructions", font=subtitle_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG).pack(anchor="w", pady=(0, 15))

        setup_steps = [
            "Connect KeyVox to your computer via USB.",
            "Open the KeyVox App (pre-installed or downloadable).",
            "Follow the voice enrollment process.",
            "You will be asked to record a short phrase 3-5 times in a quiet environment. The system will use these samples to create a secure voiceprint.",
            "Set up your preferred authentication protocols: Choose between FIDO, OATH, or challenge response options depending on the services you want to link."
        ]
        
        body_font = font.Font(family=FONT_FAMILY, size=12)
        for i, step in enumerate(setup_steps, 1):
            tk.Label(left_frame, text=f"{i}. {step}", font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left", wraplength=350).pack(anchor="w", pady=4)
        
        right_frame = tk.Frame(content_frame, bg=INFO_CARD_BG)
        right_frame.grid(row=1, column=1, sticky="nw", padx=(20, 0))

        tk.Label(right_frame, text="Security Tips", font=subtitle_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG).pack(anchor="w", pady=(0, 15))

        security_tips = [
            "Enroll in a quiet environment for better accuracy.",
            "Update your voice model if you're sick or your voice changes significantly.",
            "Never share recordings of your voice used for authentication."
        ]

        for i, tip in enumerate(security_tips, 1):
            tk.Label(right_frame, text=f"{i}. {tip}", font=body_font, fg=INFO_CARD_TEXT, bg=INFO_CARD_BG, justify="left", wraplength=350).pack(anchor="w", pady=4)

    def show_insert_key_screen(self):
        self.login_flow_state = 'not_started'
        self.currently_logged_in_user = None; self.login_attempt_user = None
        card = self._create_main_card(width=500, height=350)
        self._update_nav_selection("home")
        content_wrapper = tk.Frame(card, bg=CARD_BG_COLOR); content_wrapper.pack(expand=True)
        tk.Label(content_wrapper, image=self.key_img, bg=CARD_BG_COLOR).pack(pady=(20, 10))
        if not self.enrolled_users:
            tk.Label(content_wrapper, text="Welcome to Key Vox", font=self.font_large, fg=TEXT_COLOR, bg=CARD_BG_COLOR).pack(pady=10)
            tk.Label(content_wrapper, text="No users enrolled. Go to Enrollment tab to start.",font=self.font_normal, fg=TEXT_COLOR, bg=CARD_BG_COLOR, justify="center").pack(pady=20)
        else:
            tk.Label(content_wrapper, text="Insert Your Key", font=self.font_large, fg=TEXT_COLOR, bg=CARD_BG_COLOR).pack(pady=10)
            tk.Button(content_wrapper, text="Begin Login", font=self.font_normal, bg=BUTTON_LIGHT_COLOR, fg=BUTTON_LIGHT_TEXT_COLOR, command=self.show_login_voice_auth_screen, padx=20, pady=5, relief="flat").pack(pady=20)

    def show_logged_in_screen(self):
        self.login_flow_state = 'logged_in'
        card = self._create_main_card(width=600, height=350)
        
        card.grid_columnconfigure(0, weight=2)
        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(1, weight=1)
        card.grid_rowconfigure(2, weight=1)

        tk.Label(card,text="Security Token Detected",font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=0,columnspan=2,pady=(30,25),padx=40,sticky="w")
        
        details_frame=tk.Frame(card,bg=CARD_BG_COLOR)
        details_frame.grid(row=1,column=0,sticky="nw", padx=40)
        tk.Label(details_frame,text="Token ID:",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=0,sticky="w",padx=(0,20))
        tk.Label(details_frame,text=self.token_id,font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=1,sticky="w")
        tk.Label(details_frame,text="Last Sync:",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=1,column=0,sticky="w",pady=(10,0),padx=(0,20))
        tk.Label(details_frame,text=f"{int(time.time())%10+2} seconds ago",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=1,column=1,sticky="w",pady=(10,0))
        
        tk.Button(card,text="Manage Applications",font=self.font_normal,bg=BUTTON_COLOR,fg=TEXT_COLOR,relief="flat",borderwidth=0,padx=30,pady=8, command=self.show_applications_screen).grid(row=2,column=0,pady=(20,30),padx=40,sticky="sw")
        
        tk.Label(card, image=self.usb_img, bg=CARD_BG_COLOR).grid(row=1, column=1, rowspan=2, padx=(0, 40), sticky="e")

    def show_login_voice_auth_screen(self):
        self.login_flow_state = 'voice_auth'
        if not self.enrolled_users: messagebox.showerror("Login Error", "No users are enrolled. Please enroll a user first."); return
        self.login_attempt_user = self.enrolled_users[0]
        card = self._create_main_card(width=600, height=350)
        self._update_nav_selection("home")
        tk.Label(card,text="Please say 'My password is my voice'",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(expand=True)
        mic_label = tk.Label(card, image=self.mic_img, bg=CARD_BG_COLOR, cursor="hand2"); mic_label.pack(expand=True)
        mic_label.bind("<Button-1>", self._simulate_login_voice_record)
        self.recording_status_label=tk.Label(card,text="Click the mic to authenticate",font=self.font_small,fg=TEXT_COLOR,bg=CARD_BG_COLOR);self.recording_status_label.pack(pady=(0, 20))
    
    def _simulate_login_voice_record(self, event=None):
        self.recording_status_label.config(text="Authenticating..."); self.root.update_idletasks(); time.sleep(1.5)
        messagebox.showinfo("Success", "Voice Authenticated!"); self.show_password_screen()
    
    def show_password_screen(self):
        self.login_flow_state = 'password_entry'
        card = self._create_main_card(width=500, height=350)
        self._update_nav_selection("home")
        content_wrapper = tk.Frame(card, bg=CARD_BG_COLOR); content_wrapper.pack(expand=True)
        tk.Label(content_wrapper,text="Enter Password",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(pady=(20,10));self.error_label=tk.Label(content_wrapper,text="",font=self.font_small,fg=ERROR_COLOR,bg=CARD_BG_COLOR);self.error_label.pack(pady=(0,10))
        self.password_entry=tk.Entry(content_wrapper,font=self.font_large,fg=TEXT_COLOR,bg=GRADIENT_TOP_COLOR,show="*",width=25,relief="solid",borderwidth=1,justify="center");self.password_entry.pack(pady=10,ipady=5);self.password_entry.focus_set()
        tk.Button(content_wrapper,text="Confirm",font=self.font_normal,bg=BUTTON_COLOR,fg=TEXT_COLOR,relief="flat",borderwidth=0,padx=20,pady=5,command=self.check_password).pack(pady=(20,15))
        forgot_link=tk.Label(content_wrapper,text="Forgot Password?",font=self.font_small,fg=TEXT_COLOR,bg=CARD_BG_COLOR,cursor="hand2");forgot_link.pack();forgot_link.bind("<Button-1>",self.show_forgot_password_email_screen)
    
    def check_password(self):
        if not self.login_attempt_user: messagebox.showerror("Error", "Login error."); self.show_home_screen(); return
        if self.password_entry.get()==self.login_attempt_user['password']:
            self.currently_logged_in_user = self.login_attempt_user; self.login_attempt_user = None; self.show_home_screen()
        else: self.error_label.config(text="Incorrect Password."); self.password_entry.delete(0, 'end')

    def show_forgot_password_email_screen(self, event=None):
        self.login_flow_state = 'password_reset_email'
        if not self.login_attempt_user: messagebox.showerror("Error", "No user context."); self.show_home_screen(); return
        self.password_reset_otp = None
        card = self._create_main_card(width=600, height=400)
        self._update_nav_selection("home")
        tk.Label(card, text="Reset Password", font=self.font_large_bold, fg=TEXT_COLOR, bg=CARD_BG_COLOR).grid(row=0, column=0, columnspan=3, sticky="w", pady=(20, 20), padx=40)
        tk.Label(card, text="Email:", font=self.font_large, fg=TEXT_COLOR, bg=CARD_BG_COLOR).grid(row=1, column=0, sticky="w", pady=5, padx=(40, 10))
        self.reset_email_entry = tk.Entry(card, font=self.font_large, width=25, bg=GRADIENT_TOP_COLOR, fg=TEXT_COLOR, relief="solid", bd=1); self.reset_email_entry.grid(row=1, column=1, columnspan=2, pady=5, ipady=4, sticky="ew", padx=(0, 40))
        tk.Label(card, text="Code:", font=self.font_large, fg=TEXT_COLOR, bg=CARD_BG_COLOR).grid(row=2, column=0, sticky="w", pady=5, padx=(40, 10))
        self.reset_otp_entry = tk.Entry(card, font=self.font_large, width=15, bg=GRADIENT_TOP_COLOR, fg=TEXT_COLOR, relief="solid", bd=1); self.reset_otp_entry.grid(row=2, column=1, pady=5, ipady=4, sticky="w")
        tk.Button(card, text="Send Code", font=self.font_normal, bg=BUTTON_LIGHT_COLOR, fg=BUTTON_LIGHT_TEXT_COLOR, relief="flat", command=self._send_reset_otp).grid(row=2, column=2, sticky="e", padx=(10, 40))
        self.reset_error_label = tk.Label(card, text="", font=self.font_small, fg=ERROR_COLOR, bg=CARD_BG_COLOR); self.reset_error_label.grid(row=3, column=0, columnspan=3, pady=(10, 0))
        tk.Button(card, text="Verify Code", font=self.font_normal, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief="flat", padx=15, pady=5, command=self._verify_reset_otp).grid(row=4, column=0, columnspan=3, pady=(20, 10))
        back_link = tk.Label(card, text="< Back to Login", font=self.font_small, fg=TEXT_COLOR, bg=CARD_BG_COLOR, cursor="hand2"); back_link.grid(row=5, column=0, columnspan=3, pady=5); back_link.bind("<Button-1>", lambda e: self.show_password_screen())

    def _send_reset_otp(self):
        email = self.reset_email_entry.get()
        if not email or "@" not in email or "." not in email: self.reset_error_label.config(text="Please enter a valid email address.", fg=ERROR_COLOR); return
        if email != self.login_attempt_user.get('email'): self.reset_error_label.config(text="Email does not match user account.", fg=ERROR_COLOR); return
        self.password_reset_otp = str(random.randint(100000, 999999)); messagebox.showinfo("Simulated OTP", f"Code sent to {email}.\nYour code is: {self.password_reset_otp}"); self.reset_error_label.config(text=f"Code sent to {self._mask_email(email)}", fg=TEXT_COLOR)

    def _verify_reset_otp(self):
        if self.password_reset_otp is None: self.reset_error_label.config(text="Please click 'Send Code' first.", fg=ERROR_COLOR); return
        if self.reset_otp_entry.get() != self.password_reset_otp: self.reset_error_label.config(text="Invalid code. Please try again.", fg=ERROR_COLOR); return
        self.show_forgot_password_new_pw_screen()

    def show_forgot_password_new_pw_screen(self):
        self.login_flow_state = 'password_reset_new_pw'
        card = self._create_main_card(width=600, height=350)
        self._update_nav_selection("home")
        tk.Label(card, text="Set New Password", font=self.font_large_bold, fg=TEXT_COLOR, bg=CARD_BG_COLOR).grid(row=0, column=0, columnspan=2, sticky="w", pady=(20, 20), padx=40)
        tk.Label(card, text="New Password:", font=self.font_large, fg=TEXT_COLOR, bg=CARD_BG_COLOR).grid(row=1, column=0, sticky="w", pady=5, padx=(40, 10))
        self.reset_pw1_entry = tk.Entry(card, font=self.font_large, width=25, bg=GRADIENT_TOP_COLOR, fg=TEXT_COLOR, show="*", relief="solid", bd=1); self.reset_pw1_entry.grid(row=1, column=1, pady=5, ipady=4, sticky="ew", padx=(0,40))
        tk.Label(card, text="Confirm:", font=self.font_large, fg=TEXT_COLOR, bg=CARD_BG_COLOR).grid(row=2, column=0, sticky="w", pady=5, padx=(40, 10))
        self.reset_pw2_entry = tk.Entry(card, font=self.font_large, width=25, bg=GRADIENT_TOP_COLOR, fg=TEXT_COLOR, show="*", relief="solid", bd=1); self.reset_pw2_entry.grid(row=2, column=1, pady=5, ipady=4, sticky="ew", padx=(0,40))
        self.reset_pw_error_label = tk.Label(card, text="", font=self.font_small, fg=ERROR_COLOR, bg=CARD_BG_COLOR); self.reset_pw_error_label.grid(row=3, column=0, columnspan=2, pady=(10,0))
        tk.Button(card, text="Reset Password", font=self.font_normal, bg=BUTTON_COLOR, fg=TEXT_COLOR, relief="flat", padx=15, pady=5, command=self._process_password_reset).grid(row=4, column=0, columnspan=2, pady=(20, 10))

    def _process_password_reset(self):
        new_pw1,new_pw2 = self.reset_pw1_entry.get(), self.reset_pw2_entry.get()
        if not new_pw1 or not new_pw2: self.reset_pw_error_label.config(text="Password fields cannot be empty."); return
        if new_pw1 != new_pw2: self.reset_pw_error_label.config(text="Passwords do not match."); return
        self.login_attempt_user['password'] = new_pw1; self._save_data_to_file(); messagebox.showinfo("Success", "Password has been reset."); self.password_reset_otp = None; self.show_password_screen()

    # --- APPLICATIONS ---
    def show_applications_screen(self):
        self._update_nav_selection("applications")
        if not self.currently_logged_in_user:
            card = self._create_main_card(width=600, height=300)
            tk.Label(card, text="Please log in to manage application settings.", font=self.font_large, fg=TEXT_COLOR, bg=CARD_BG_COLOR, wraplength=400).pack(expand=True)
            return
        
        user = self.currently_logged_in_user
        card = self._create_main_card(width=780, height=380)
        cards_frame=tk.Frame(card,bg=CARD_BG_COLOR); cards_frame.pack(expand=True)
        pw_card=self._create_app_card(cards_frame); tk.Label(pw_card, image=self.key_img, bg=CARD_BG_COLOR).pack(pady=(20,0)); tk.Label(pw_card,text="Password",font=self.font_medium_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(pady=(10,5));tk.Label(pw_card,text=len(user.get('password',''))*'•',font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(pady=5);tk.Button(pw_card,text="Edit Password",font=self.font_small,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="solid",bd=1,padx=10,command=self.show_edit_password_screen).pack(side=tk.BOTTOM,pady=(10,15))
        voice_card=self._create_app_card(cards_frame); tk.Label(voice_card, image=self.mic_img, bg=CARD_BG_COLOR).pack(pady=(20,0)); tk.Label(voice_card,text="Voice Biometrics",font=self.font_medium_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(pady=(10,5));tk.Label(voice_card,text=f"Status: {user.get('voice_status','Not Enrolled')}",font=self.font_normal,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(pady=5);tk.Button(voice_card,text="Edit Biometrics",font=self.font_small,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="solid",bd=1,padx=10,command=self._start_edit_voice_flow).pack(side=tk.BOTTOM,pady=(10,15))
        otp_card=self._create_app_card(cards_frame); tk.Label(otp_card, image=self.otp_img, bg=CARD_BG_COLOR).pack(pady=(20,0)); tk.Label(otp_card,text="OTP Settings",font=self.font_medium_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(pady=(10,5));masked_email=self._mask_email(user.get('email',''));tk.Label(otp_card,text="Account:",font=self.font_normal,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(pady=(5,0));tk.Label(otp_card,text=masked_email,font=self.font_normal,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(pady=(0,5));tk.Button(otp_card,text="Edit Email Address",font=self.font_small,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="solid",bd=1,padx=10,command=self.show_edit_email_screen).pack(side=tk.BOTTOM,pady=(10,15))

    def _create_app_card(self,p):
        c=tk.Frame(p,bg=CARD_BG_COLOR,width=220,height=280,relief="solid",bd=1);c.pack(side="left",padx=15,pady=20);c.pack_propagate(False);return c
    
    def show_edit_password_screen(self):
        card = self._create_main_card(width=650, height=400)
        self._update_nav_selection("applications")
        tk.Label(card,text="Change Your Password",font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=0,columnspan=2,sticky="w",pady=(20,20), padx=40);
        fields={"Old Password:":'old_pw',"New Password:":'new_pw1',"Confirm New:":'new_pw2'};self.edit_pw_entries={}
        for i,(label,key) in enumerate(fields.items()):
            tk.Label(card,text=label,font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=i+1,column=0,sticky="w",pady=5,padx=(40,20));entry=tk.Entry(card,font=self.font_large,width=20,bg=GRADIENT_TOP_COLOR,fg=TEXT_COLOR,show="*",relief="solid",bd=1);entry.grid(row=i+1,column=1,pady=5,ipady=4, padx=(0,40));self.edit_pw_entries[key]=entry
        self.edit_pw_error=tk.Label(card,text="",font=self.font_small,fg=ERROR_COLOR,bg=CARD_BG_COLOR);self.edit_pw_error.grid(row=4,column=0,columnspan=2,pady=10);tk.Button(card,text="Save Changes",font=self.font_normal,bg=BUTTON_COLOR,fg=TEXT_COLOR,relief="flat",padx=15,pady=5,command=self._process_password_change).grid(row=5,column=0,columnspan=2,pady=10)
    
    def _process_password_change(self):
        old,new1,new2=self.edit_pw_entries['old_pw'].get(),self.edit_pw_entries['new_pw1'].get(),self.edit_pw_entries['new_pw2'].get()
        if old != self.currently_logged_in_user['password']:self.edit_pw_error.config(text="Old password is not correct.");return
        if not new1:self.edit_pw_error.config(text="New password cannot be empty.");return
        if new1 != new2:self.edit_pw_error.config(text="New passwords do not match.");return
        self.currently_logged_in_user['password'] = new1; self._save_data_to_file(); messagebox.showinfo("Success", "Password updated!");self.show_applications_screen()

    def show_edit_email_screen(self):
        card = self._create_main_card(width=650, height=400)
        self._update_nav_selection("applications")
        tk.Label(card,text="Change Email Address",font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=0,columnspan=3,sticky="w",pady=(20,20), padx=40)
        tk.Label(card,text="New Email:",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=1,column=0,sticky="w",pady=5,padx=(40,20))
        self.edit_email_entry=tk.Entry(card,font=self.font_large,width=25,bg=GRADIENT_TOP_COLOR,fg=TEXT_COLOR,relief="solid",bd=1);self.edit_email_entry.grid(row=1,column=1,columnspan=2, pady=5,ipady=4, padx=(0,40), sticky="ew")
        tk.Label(card,text="Code:",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=2,column=0,sticky="w",pady=5,padx=(40,20));self.edit_email_otp_entry=tk.Entry(card,font=self.font_large,width=15,bg=GRADIENT_TOP_COLOR,fg=TEXT_COLOR,relief="solid",bd=1);self.edit_email_otp_entry.grid(row=2,column=1,pady=5,ipady=4,sticky="w")
        tk.Button(card,text="Send Code",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",command=self._send_edit_email_otp).grid(row=2,column=2,sticky="e", padx=(0,40));self.edit_email_error=tk.Label(card,text="",font=self.font_small,fg=ERROR_COLOR,bg=CARD_BG_COLOR);self.edit_email_error.grid(row=3,column=0,columnspan=3,pady=10);tk.Button(card,text="Save Changes",font=self.font_normal,bg=BUTTON_COLOR,fg=TEXT_COLOR,relief="flat",padx=15,pady=5,command=self._process_email_change).grid(row=4,column=0,columnspan=3,pady=10)

    def _send_edit_email_otp(self):
        email=self.edit_email_entry.get()
        if"@"not in email or"."not in email:self.edit_email_error.config(text="Invalid email address.");return
        self.password_reset_otp=str(random.randint(100000,999999));messagebox.showinfo("Simulated OTP",f"OTP sent to {email}.\nCode: {self.password_reset_otp}");self.edit_email_error.config(text="")
    
    def _process_email_change(self):
        if not self.password_reset_otp:self.edit_email_error.config(text="Please send a code first.");return
        if self.edit_email_otp_entry.get()!=self.password_reset_otp:self.edit_email_error.config(text="Invalid OTP code.");return
        self.currently_logged_in_user['email']=self.edit_email_entry.get();self._save_data_to_file();messagebox.showinfo("Success","Email updated!");self.show_applications_screen()
    
    def _start_edit_voice_flow(self):
        self.enrollment_state = 'editing_voice'; self.current_phrase_index = 0; self.show_enrollment_voice_record()

    # --- ENROLLMENT FLOW ---
    def navigate_to_enrollment(self, event=None):
        resume_map = {'step1_account_setup': self.show_enrollment_step1, 'step2_voice_intro': self.show_enrollment_step2, 'step3_voice_record': self.show_enrollment_voice_record, 'step4_otp': self.show_enrollment_step3_otp, 'complete': self.show_enrollment_summary}
        if self.enrollment_state in resume_map: resume_map[self.enrollment_state]()
        else: self.show_enrollment_step1()

    def show_enrollment_step1(self):
        self.enrollment_state='step1_account_setup'
        self.new_enrollment_data={}; self.simulated_enrollment_otp=None
        card = self._create_main_card(width=700, height=450)
        self._update_nav_selection("enrollment")
        tk.Label(card,text="STEP 1: Account Setup",font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=0,columnspan=2,sticky="w",pady=(20,5), padx=40);
        tk.Label(card,text="Enter your basic account information",font=self.font_normal,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=1,column=0,columnspan=2,sticky="w",pady=(0,25), padx=40)
        fields=["Full Name:","Username:","Password:","Confirm Password:"];self.entry_widgets=[]
        for i,field in enumerate(fields):
            tk.Label(card,text=field,font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=i+2,column=0,sticky="w",pady=8,padx=(40,20));entry=tk.Entry(card,font=self.font_large,width=25,bg=GRADIENT_TOP_COLOR,fg=TEXT_COLOR,relief="solid",bd=1);self.entry_widgets.append(entry)
            if"Password"in field:entry.config(show="*")
            entry.grid(row=i+2,column=1,pady=8,ipady=4, padx=(0,40))
        self.full_name_entry,self.username_entry,self.enroll_password_entry,self.confirm_password_entry=self.entry_widgets
        self.enroll_error_label=tk.Label(card,text="",font=self.font_small,fg=ERROR_COLOR,bg=CARD_BG_COLOR);self.enroll_error_label.grid(row=len(fields)+2,column=0,columnspan=2,pady=(10,0));
        bf=tk.Frame(self.content_frame,bg="#7c2e50");bf.pack(fill="x",padx=60,pady=(0,10));tk.Label(bf,text="● ○ ○",font=self.font_large,fg=TEXT_COLOR,bg="#7c2e50").pack(side="left");tk.Button(bf,text="Next Step →",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",padx=15,pady=5,command=self._validate_step1).pack(side="right")
    
    def _validate_step1(self):
        entries=[e.get() for e in self.entry_widgets]
        if not all(entries):self.enroll_error_label.config(text="All fields are required.");return
        if any(u['username']==entries[1] for u in self.enrolled_users):self.enroll_error_label.config(text="Username already exists.");return
        if entries[2]!=entries[3]:self.enroll_error_label.config(text="Passwords do not match.");return
        self.new_enrollment_data={"full_name":entries[0],"username":entries[1],"password":entries[2],"voice_status":"Enrolled"};self.enrollment_state='step2_voice_intro';self.enroll_error_label.config(text="");self.current_phrase_index=0;self.show_enrollment_step2()
    
    def show_enrollment_step2(self):
        self.enrollment_state = 'step2_voice_intro'
        card = self._create_main_card(width=700, height=350)
        self._update_nav_selection("enrollment")
        tk.Label(card,text="STEP 2: Voice Authentication",font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(anchor="w",pady=(20,5), padx=40);tk.Label(card,text="Record your voice for added security. You will record 5 phrases. This will\nallow the system to recognize your unique voiceprint for authentication.",font=self.font_normal,fg=TEXT_COLOR,bg=CARD_BG_COLOR, justify="left").pack(anchor="w",pady=(0,25), padx=40);
        bf=tk.Frame(self.content_frame,bg="#7c2e50");bf.pack(fill="x",padx=60,pady=(0,10));tk.Button(bf,text="< Back",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",padx=15,pady=5,command=self.show_enrollment_step1).pack(side="left");tk.Label(bf,text="○ ● ○",font=self.font_large,fg=TEXT_COLOR,bg="#7c2e50").pack(side="left",padx=20);tk.Button(bf,text="Start →",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",padx=15,pady=5,command=self._start_voice_recording).pack(side="right")
    
    def _start_voice_recording(self):self.enrollment_state='step3_voice_record';self.show_enrollment_voice_record()

    def show_enrollment_voice_record(self):
        if self.enrollment_state != 'editing_voice': self.enrollment_state = 'step3_voice_record'
        is_editing=self.enrollment_state=='editing_voice'
        card = self._create_main_card(width=600,height=350)
        self._update_nav_selection("applications" if is_editing else "enrollment")
        tk.Label(card,text=f"{self.current_phrase_index+1} of 5:",font=self.font_normal,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(pady=(20,0));tk.Label(card,text=f'"{self.enrollment_phrases[self.current_phrase_index]}"',font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR,wraplength=500).pack(expand=True)
        mic_label = tk.Label(card,image=self.mic_img,bg=CARD_BG_COLOR,highlightthickness=0,cursor="hand2");mic_label.pack(pady=10)
        mic_label.bind("<Button-1>",self.toggle_recording)
        self.recording_status_label=tk.Label(card,text="Click the mic to record",font=self.font_small,fg=TEXT_COLOR,bg=CARD_BG_COLOR);self.recording_status_label.pack(pady=(0,20));
        bf=tk.Frame(self.content_frame,bg="#7c2e50");bf.pack(fill="x",padx=60,pady=(0,10));tk.Button(bf,text="< Back",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",padx=15,pady=5,command=self._go_back_phrase).pack(side="left")
        self.next_btn=tk.Button(bf,text="Next →"if not(is_editing and self.current_phrase_index==4)else"Finish",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",padx=15,pady=5,command=self._go_next_phrase,state="disabled");self.next_btn.pack(side="right")
    
    def _go_back_phrase(self):
        if self.current_phrase_index>0:self.current_phrase_index-=1;self.show_enrollment_voice_record()
        elif self.enrollment_state=='editing_voice':self.show_applications_screen()
        else:self.enrollment_state='step2_voice_intro';self.show_enrollment_step2()

    def _go_next_phrase(self):
        if self.current_phrase_index<len(self.enrollment_phrases)-1:self.current_phrase_index+=1;self.show_enrollment_voice_record()
        elif self.enrollment_state=='editing_voice':self.currently_logged_in_user['voice_status']='Enrolled';self._save_data_to_file();messagebox.showinfo("Success","Biometrics updated!");self.show_applications_screen()
        else:self.enrollment_state='step4_otp';self.show_enrollment_step3_otp()
    
    def show_enrollment_step3_otp(self):
        self.enrollment_state = 'step4_otp'
        card = self._create_main_card(width=700, height=400)
        self._update_nav_selection("enrollment")
        tk.Label(card,text="STEP 3: OTP Verification",font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=0,columnspan=3,sticky="w",pady=(20,5), padx=40);tk.Label(card,text="Verify your email using the code we sent to your inbox.",font=self.font_normal,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=1,column=0,columnspan=3,sticky="w",pady=(0,25), padx=40);
        tk.Label(card,text="Email Address:",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=2,column=0,sticky="w",pady=10,padx=(40,20));self.otp_email_entry=tk.Entry(card,font=self.font_large,width=25,bg=GRADIENT_TOP_COLOR,fg=TEXT_COLOR,relief="solid",bd=1);self.otp_email_entry.grid(row=2,column=1,columnspan=2,pady=10,ipady=4, padx=(0,40));
        tk.Label(card,text="Code:",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=3,column=0,sticky="w",pady=10,padx=(40,20));self.otp_entry=tk.Entry(card,font=self.font_large,width=15,bg=GRADIENT_TOP_COLOR,fg=TEXT_COLOR,relief="solid",bd=1);self.otp_entry.grid(row=3,column=1,pady=10,ipady=4,sticky="w")
        tk.Button(card,text="Send Code",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",command=self._send_otp_simulation).grid(row=3,column=2,sticky="w",padx=10);self.otp_error_label=tk.Label(card,text="",font=self.font_small,fg=ERROR_COLOR,bg=CARD_BG_COLOR);self.otp_error_label.grid(row=4,column=0,columnspan=3,pady=(10,0));
        bf=tk.Frame(self.content_frame,bg="#7c2e50");bf.pack(fill="x",padx=60,pady=(0,10));tk.Button(bf,text="< Back",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",padx=15,pady=5,command=self.show_enrollment_step2).pack(side="left");tk.Label(bf,text="○ ○ ●",font=self.font_large,fg=TEXT_COLOR,bg="#7c2e50").pack(side="left",padx=20);tk.Button(bf,text="Next Step →",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",padx=15,pady=5,command=self._verify_otp).pack(side="right")
    
    def _send_otp_simulation(self):
        email=self.otp_email_entry.get()
        if"@"not in email or"."not in email:self.otp_error_label.config(text="Please enter a valid email address.");return
        self.simulated_enrollment_otp=str(random.randint(100000,999999));messagebox.showinfo("Simulated OTP",f"OTP sent to {email}.\n\nCode is: {self.simulated_enrollment_otp}");self.otp_error_label.config(text="")
    
    def _verify_otp(self):
        if not self.simulated_enrollment_otp:self.otp_error_label.config(text="Please click 'Send Code' first.");return
        if self.otp_entry.get()==self.simulated_enrollment_otp:self.new_enrollment_data['email']=self.otp_email_entry.get();self.enrollment_state='complete';self.show_enrollment_summary()
        else:self.otp_error_label.config(text="Invalid OTP. Please try again.")
    
    def show_enrollment_summary(self):
        self.enrollment_state = 'complete'
        card = self._create_main_card(width=700, height=450)
        self._update_nav_selection("enrollment")
        tk.Label(card,text="Enrollment Process Complete",font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=0,columnspan=2,sticky="w",pady=(20,5), padx=40);tk.Label(card,text="You've successfully enrolled. Your credentials are now securely registered.",font=self.font_normal,fg=TEXT_COLOR,bg=CARD_BG_COLOR,justify="left").grid(row=1,column=0,columnspan=2,sticky="w",pady=(0,25), padx=40)
        summary_data={"Full Name:":self.new_enrollment_data.get('full_name'),"Username:":self.new_enrollment_data.get('username'),"Password:":len(self.new_enrollment_data.get('password',''))*'•',"Email:":self.new_enrollment_data.get('email'),"Voice Pattern:":"Saved"}
        for i,(label,value)in enumerate(summary_data.items()):tk.Label(card,text=label,font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=i+2,column=0,sticky="w",pady=5, padx=40);tk.Label(card,text=value,font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=i+2,column=1,sticky="w",pady=5,padx=20)
        tk.Button(card,text="Finish",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",padx=30,pady=5,command=self._finish_enrollment).grid(row=len(summary_data)+2,column=0,columnspan=2,pady=30)
    
    def _finish_enrollment(self):
        self.enrolled_users.append(self.new_enrollment_data);self._save_data_to_file();messagebox.showinfo("Success","New user enrollment complete!");self.just_enrolled=True;self.enrollment_state='not_started';self.show_home_screen()
    
    # --- AUDIO & UTILITIES ---
    def toggle_recording(self,event=None):
        if self.is_recording: self.is_recording=False; self.recording_status_label.config(text="Saving...")
        else:
            self.is_recording=True; self.next_btn.config(state="disabled"); self.recording_status_label.config(text="Recording... Click mic to stop.")
            self.recording_thread=threading.Thread(target=self._record_audio_thread, daemon=True); self.recording_thread.start()

    def _record_audio_thread(self):
        username="user"
        if self.enrollment_state=='editing_voice':username=self.currently_logged_in_user.get('username','user')
        else:username=self.new_enrollment_data.get('username','user')
        filepath=os.path.join(AUDIO_DIR,f"{username}_phrase_{self.current_phrase_index+1}.wav")
        stream=self.pyaudio_instance.open(format=FORMAT,channels=CHANNELS,rate=RATE,input=True,frames_per_buffer=CHUNK);frames=[]
        while self.is_recording:frames.append(stream.read(CHUNK,exception_on_overflow=False))
        stream.stop_stream();stream.close()
        with wave.open(filepath,'wb')as wf:wf.setnchannels(CHANNELS);wf.setsampwidth(self.pyaudio_instance.get_sample_size(FORMAT));wf.setframerate(RATE);wf.writeframes(b''.join(frames))
        self.root.after(0,self._on_recording_finished)
    
    def _on_recording_finished(self):
        self.recording_status_label.config(text=f"Recording saved!"); self.next_btn.config(state="normal")
    
    def _mask_email(self,e):
        if not e or'@'not in e: return ""
        p, d = e.split('@', 1)
        if len(p) == 0: return f"***@{d}"
        if len(p) <= 3: return f"{p[0]}***@{d}"
        return f"{p[:2]}***{p[-1]}@{d}"

    def _on_closing(self):
        self.is_recording=False
        if self.recording_thread and self.recording_thread.is_alive():
            self.root.after(100, self._shutdown)
        else:
            self._shutdown()
            
    def _shutdown(self):
        self.pyaudio_instance.terminate();self.root.destroy()
        
if __name__=="__main__":
    if not os.path.exists("images"): os.makedirs("images")
    def create_dummy_image(path, size, color):
        if not os.path.exists(path):
            try:
                img = Image.new('RGBA', size, color); img.save(path, 'PNG')
            except Exception as e: print(f"Could not create dummy image {path}: {e}")
    
    create_dummy_image("images/logo.png", (120, 40), "#FFFFFF")
    create_dummy_image("images/key.png", (60, 60), "#FFFFFF")
    create_dummy_image("images/mic.png", (60, 60), "#FFFFFF")
    create_dummy_image("images/otp_settings.png", (60, 60), "#FFFFFF")
    create_dummy_image("images/usb.png", (180, 180), "#FFFFFF") 

    root=tk.Tk()
    app=KeyVoxApp(root)
    root.mainloop()