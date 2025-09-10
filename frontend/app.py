import tkinter as tk
from tkinter import font, messagebox, simpledialog
import time
import os
import wave
import pyaudio
import threading
from PIL import Image, ImageTk
from api_client import APIClient  # <-- IMPORT your new API client

# --- UI Configuration (Unchanged) ---
GRADIENT_TOP_COLOR = "#5e213f"; GRADIENT_BOTTOM_COLOR = "#983a62"; CARD_BG_COLOR = "#6a2f4b"
TEXT_COLOR = "#ffffff"; BUTTON_COLOR = "#c8356e"; BUTTON_LIGHT_COLOR = "#f0f0f0"
BUTTON_LIGHT_TEXT_COLOR = "#333333"; ERROR_COLOR = "#ff6b6b"; FONT_FAMILY = "Segoe UI"; PLACEHOLDER_COLOR = "#333333"

# --- Frontend Configuration ---
AUDIO_DIR = "temp_audio"
CHUNK = 1024; FORMAT = pyaudio.paInt16; CHANNELS = 1; RATE = 44100

class KeyVoxApp:
    def __init__(self, root):
        self.root = root
        self.width, self.height = 900, 600
        self.root.title("Key Vox"); self.root.geometry(f"{self.width}x{self.height}"); self.root.resizable(False, False)
        if not os.path.exists(AUDIO_DIR): os.makedirs(AUDIO_DIR)
        
        # --- Instantiate the API Client ---
        self.api = APIClient()

        # --- Image loading ---
        try:
            self.logo_img = ImageTk.PhotoImage(Image.open("assets/images/logo.png").resize((110, 110), Image.Resampling.LANCZOS))
            self.key_img = ImageTk.PhotoImage(Image.open("assets/images/key.png").resize((60, 60), Image.Resampling.LANCZOS))
            self.mic_img = ImageTk.PhotoImage(Image.open("assets/images/mic.png").resize((60, 60), Image.Resampling.LANCZOS))
            self.otp_img = ImageTk.PhotoImage(Image.open("assets/images/otp_settings.png").resize((60, 60), Image.Resampling.LANCZOS))
            self.usb_img = ImageTk.PhotoImage(Image.open("assets/images/usb.png").resize((230, 230), Image.Resampling.LANCZOS))
        except FileNotFoundError as e:
            messagebox.showerror("Asset Error", f"Image not found: {e.filename}\nPlease ensure the 'assets/images' folder is correct.")
            root.destroy(); return
            
        # --- Frontend State Management ---
        self.currently_logged_in_user = None
        self.login_attempt_user = None 
        self.new_enrollment_data = {} 
        self.is_recording = False
        self.pyaudio_instance = pyaudio.PyAudio()

        # --- UI State Variables  ---
        self.token_id = "f3d4-9a7b-23ce-8e6f"; self.just_enrolled = False
        self.login_flow_state = 'not_started'; self.enrollment_state = 'not_started'
        self.enrollment_phrase = "My voice is my password"
        self.nav_widgets = {}

        # --- Font and Canvas Setup  ---
        self.font_nav=font.Font(family=FONT_FAMILY,size=12); self.font_nav_active=font.Font(family=FONT_FAMILY,size=12,weight="bold"); self.font_large_bold=font.Font(family=FONT_FAMILY,size=20,weight="bold"); self.font_large=font.Font(family=FONT_FAMILY,size=16); self.font_medium_bold=font.Font(family=FONT_FAMILY,size=14,weight="bold"); self.font_normal=font.Font(family=FONT_FAMILY,size=10); self.font_small=font.Font(family=FONT_FAMILY,size=9)
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, highlightthickness=0); self.canvas.pack(fill="both", expand=True); self._create_gradient(GRADIENT_TOP_COLOR, GRADIENT_BOTTOM_COLOR); self._create_header()
        self.content_frame = tk.Frame(self.canvas, bg="#7c2e50"); self.canvas.create_window(self.width/2, self.height/2 + 60, window=self.content_frame, anchor="center")
        
        self.check_server_and_start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def check_server_and_start(self):
        """Check if the backend is running before showing the main screen."""
        if not self.api.check_server_status():
            messagebox.showerror("Connection Error", "Could not connect to the backend server.\nPlease ensure the server is running and try again.")
            self.root.destroy()
        else:
            print("✅ Backend server connected.")
            self.show_home_screen()
    
    # --- DATA & UI HELPERS ---

    def _create_gradient(self, c1, c2):
        r1,g1,b1=self.root.winfo_rgb(c1);r2,g2,b2=self.root.winfo_rgb(c2);r,g,b=(r2-r1)/self.height,(g2-g1)/self.height,(b2-b1)/self.height
        for i in range(self.height):self.canvas.create_line(0,i,self.width,i,fill=f"#{int(r1+r*i):04x}{int(g1+g*i):04x}{int(b1+b*i):04x}")
    
    def _create_header(self):
        nav_y_center=50;line_y=nav_y_center+20;side_padding=40;self.canvas.create_image(side_padding,line_y/1.2,anchor="w",image=self.logo_img,tags="logo");current_x=self.width-side_padding;info_tag="info_icon";info_rect_id=self.canvas.create_rectangle(current_x-22,nav_y_center-11,current_x,nav_y_center+11,fill=PLACEHOLDER_COLOR,outline=PLACEHOLDER_COLOR,tags=info_tag);self.canvas.create_text(current_x-11,nav_y_center,text="i",font=("Arial",12,"bold"),fill=TEXT_COLOR,tags=info_tag);self.canvas.tag_bind(info_tag,"<Button-1>",self.show_about_screen);self.canvas.tag_bind(info_tag,"<Enter>",lambda e:self.canvas.config(cursor="hand2"));self.canvas.tag_bind(info_tag,"<Leave>",lambda e:self.canvas.config(cursor=""));line_x1=self.canvas.bbox(info_rect_id)[2];current_x-=(22+10);help_tag="help_icon";self.canvas.create_rectangle(current_x-22,nav_y_center-11,current_x,nav_y_center+11,fill=PLACEHOLDER_COLOR,outline=PLACEHOLDER_COLOR,tags=help_tag);self.canvas.create_text(current_x-11,nav_y_center,text="?",font=("Arial",12,"bold"),fill=TEXT_COLOR,tags=help_tag);self.canvas.tag_bind(help_tag,"<Button-1>",self.show_help_screen);self.canvas.tag_bind(help_tag,"<Enter>",lambda e:self.canvas.config(cursor="hand2"));self.canvas.tag_bind(help_tag,"<Leave>",lambda e:self.canvas.config(cursor=""));current_x-=(22+10);self.canvas.create_oval(current_x-12,nav_y_center-6,current_x,nav_y_center+6,fill="#2ecc71",outline="");current_x-=(12+5);self.canvas.create_text(current_x,nav_y_center,text="status:",font=self.font_small,fill=TEXT_COLOR,anchor="e");start_x=180;nav_map={"home":self.show_home_screen,"Applications":self.show_applications_screen,"Enrollment":self.navigate_to_enrollment};first_tab_bbox=None
        for key,command in nav_map.items():
            text=key.capitalize();tag=f"nav_{key}";text_id=self.canvas.create_text(start_x,nav_y_center,text=text,font=self.font_nav,fill=TEXT_COLOR,anchor="w",tags=tag);self.canvas.tag_bind(tag,"<Button-1>",lambda e,cmd=command:cmd());self.canvas.tag_bind(tag,"<Enter>",lambda e:self.canvas.config(cursor="hand2"));self.canvas.tag_bind(tag,"<Leave>",lambda e:self.canvas.config(cursor=""));bbox=self.canvas.bbox(text_id)
            if first_tab_bbox is None:first_tab_bbox=bbox
            underline_id=self.canvas.create_line(bbox[0],line_y,bbox[2],line_y,fill=TEXT_COLOR,width=3,state='hidden');self.nav_widgets[key.lower()]={'text_id':text_id,'underline_id':underline_id};start_x=bbox[2]+45
        if first_tab_bbox:line_x0=first_tab_bbox[0];self.canvas.create_line(line_x0,line_y,line_x1,line_y,fill=TEXT_COLOR,width=1)
            
    def _update_nav_selection(self, key):
        if key:key=key.lower()
        for k,w in self.nav_widgets.items():self.canvas.itemconfig(w['text_id'],font=self.font_nav);self.canvas.itemconfig(w['underline_id'],state='hidden')
        if key and key in self.nav_widgets:w=self.nav_widgets[key];self.canvas.itemconfig(w['text_id'],font=self.font_nav_active);self.canvas.itemconfig(w['underline_id'],state='normal')
            
    def _clear_content_frame(self):
        for w in self.content_frame.winfo_children():w.destroy()
        self.content_frame.config(bg="#7c2e50",bd=0)

    def _create_main_card(self, width=600, height=400):
        self._clear_content_frame();card=tk.Frame(self.content_frame,bg=CARD_BG_COLOR,relief="solid",bd=1,width=width,height=height);card.pack(pady=20);card.pack_propagate(False);return card

    # --- MAIN SCREENS  ---
    def show_home_screen(self, event=None):
        self._update_nav_selection("home")
        if self.currently_logged_in_user:
            self.show_logged_in_screen()
        elif self.just_enrolled:
            self.just_enrolled = False
            self.show_login_voice_auth_screen()
        else:
            self.show_insert_key_screen()
            
    def show_about_screen(self, event=None):
       
        self._update_nav_selection(None);INFO_CARD_BG="#e9e3e6";INFO_CARD_TEXT="#3b3b3b";card=self._create_main_card(width=820,height=480);card.config(bg=INFO_CARD_BG,relief="flat",bd=0,highlightthickness=0);content_frame=tk.Frame(card,bg=INFO_CARD_BG);content_frame.pack(expand=True);title_font=font.Font(family=FONT_FAMILY,size=22,weight="bold");tk.Label(content_frame,text="About Us",font=title_font,fg=INFO_CARD_TEXT,bg=INFO_CARD_BG,justify="left").pack(anchor="w",pady=(0,20));body_font=font.Font(family=FONT_FAMILY,size=12);about_text="KeyVox is a new plug-and-play hardware authentication token that uses your unique voice as a robust and secure second factor of authentication (2FA), powered by advanced LSTM neural networks. The key is designed to work with multi-protocol systems such as FIDO U2F, OATH TOTP, challenge response system.";tk.Label(content_frame,text=about_text,font=body_font,fg=INFO_CARD_TEXT,bg=INFO_CARD_BG,justify="left",wraplength=720).pack(anchor="w",pady=(0,30));subtitle_font=font.Font(family=FONT_FAMILY,size=16,weight="bold");tk.Label(content_frame,text="How Voice Authentication Works",font=subtitle_font,fg=INFO_CARD_TEXT,bg=INFO_CARD_BG,justify="left").pack(anchor="w",pady=(0,15));tk.Label(content_frame,text="KeyVox uses LSTM-based voice biometrics to:",font=body_font,fg=INFO_CARD_TEXT,bg=INFO_CARD_BG,justify="left").pack(anchor="w",pady=(0,10));bullets=["Analyze and learn the unique patterns in your voice.","Match live voice input against your stored encrypted voiceprint.","Authenticate only if the match is within the secure threshold."];
        for bullet in bullets: tk.Label(content_frame,text=f"  •  {bullet}",font=body_font,fg=INFO_CARD_TEXT,bg=INFO_CARD_BG,justify="left",wraplength=700).pack(anchor="w",pady=2)

    def show_help_screen(self, event=None):
       
        self._update_nav_selection(None);INFO_CARD_BG="#e9e3e6";INFO_CARD_TEXT="#3b3b3b";card=self._create_main_card(width=820,height=480);card.config(bg=INFO_CARD_BG,relief="flat",bd=0,highlightthickness=0);content_frame=tk.Frame(card,bg=INFO_CARD_BG);content_frame.pack(expand=True);content_frame.grid_columnconfigure(0,weight=1);content_frame.grid_columnconfigure(1,weight=1);title_font=font.Font(family=FONT_FAMILY,size=22,weight="bold");tk.Label(content_frame,text="Need Help?",font=title_font,fg=INFO_CARD_TEXT,bg=INFO_CARD_BG).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,25));left_frame=tk.Frame(content_frame,bg=INFO_CARD_BG);left_frame.grid(row=1,column=0,sticky="nw",padx=(0,20));subtitle_font=font.Font(family=FONT_FAMILY,size=16,weight="bold");tk.Label(left_frame,text="Setup Instructions",font=subtitle_font,fg=INFO_CARD_TEXT,bg=INFO_CARD_BG).pack(anchor="w",pady=(0,15));setup_steps=["Connect KeyVox to your computer via USB.","Open the KeyVox App (pre-installed or downloadable).","Follow the voice enrollment process.","You will be asked to record a short phrase 3-5 times in a quiet environment. The system will use these samples to create a secure voiceprint.","Set up your preferred authentication protocols: Choose between FIDO, OATH, or challenge response options depending on the services you want to link."];body_font=font.Font(family=FONT_FAMILY,size=12);
        for i,step in enumerate(setup_steps,1):tk.Label(left_frame,text=f"{i}. {step}",font=body_font,fg=INFO_CARD_TEXT,bg=INFO_CARD_BG,justify="left",wraplength=350).pack(anchor="w",pady=4)
        right_frame=tk.Frame(content_frame,bg=INFO_CARD_BG);right_frame.grid(row=1,column=1,sticky="nw",padx=(20,0));tk.Label(right_frame,text="Security Tips",font=subtitle_font,fg=INFO_CARD_TEXT,bg=INFO_CARD_BG).pack(anchor="w",pady=(0,15));security_tips=["Enroll in a quiet environment for better accuracy.","Update your voice model if you're sick or your voice changes significantly.","Never share recordings of your voice used for authentication."];
        for i,tip in enumerate(security_tips,1):tk.Label(right_frame,text=f"{i}. {tip}",font=body_font,fg=INFO_CARD_TEXT,bg=INFO_CARD_BG,justify="left",wraplength=350).pack(anchor="w",pady=4)

    # --- Login Flow  ---
    def show_insert_key_screen(self):
        self.login_flow_state = 'not_started'; self.currently_logged_in_user = None; self.login_attempt_user = None
        card = self._create_main_card(width=500, height=350); self._update_nav_selection("home")
        content_wrapper = tk.Frame(card, bg=CARD_BG_COLOR); content_wrapper.pack(expand=True)
        tk.Label(content_wrapper, image=self.key_img, bg=CARD_BG_COLOR).pack(pady=(20, 10))
        tk.Label(content_wrapper, text="Welcome to Key Vox", font=self.font_large, fg=TEXT_COLOR, bg=CARD_BG_COLOR).pack(pady=10)
        tk.Button(content_wrapper, text="Begin Login", font=self.font_normal, bg=BUTTON_LIGHT_COLOR, fg=BUTTON_LIGHT_TEXT_COLOR, command=self.show_login_voice_auth_screen, padx=20, pady=5, relief="flat").pack(pady=20)
        tk.Label(content_wrapper, text="No account? Go to the Enrollment tab.",font=self.font_normal, fg=TEXT_COLOR, bg=CARD_BG_COLOR).pack(pady=10)

    def show_logged_in_screen(self):
        self.login_flow_state = 'logged_in';card=self._create_main_card(width=600,height=350);card.grid_columnconfigure(0,weight=2);card.grid_columnconfigure(1,weight=1);card.grid_rowconfigure(1,weight=1);card.grid_rowconfigure(2,weight=1);tk.Label(card,text="Security Token Detected",font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=0,columnspan=2,pady=(30,25),padx=40,sticky="w");details_frame=tk.Frame(card,bg=CARD_BG_COLOR);details_frame.grid(row=1,column=0,sticky="nw",padx=40);tk.Label(details_frame,text="Token ID:",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=0,sticky="w",padx=(0,20));tk.Label(details_frame,text=self.token_id,font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=1,sticky="w");tk.Label(details_frame,text="Last Sync:",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=1,column=0,sticky="w",pady=(10,0),padx=(0,20));tk.Label(details_frame,text=f"{int(time.time())%10+2} seconds ago",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=1,column=1,sticky="w",pady=(10,0));tk.Button(card,text="Manage Applications",font=self.font_normal,bg=BUTTON_COLOR,fg=TEXT_COLOR,relief="flat",borderwidth=0,padx=30,pady=8,command=self.show_applications_screen).grid(row=2,column=0,pady=(20,30),padx=40,sticky="sw");tk.Label(card,image=self.usb_img,bg=CARD_BG_COLOR).grid(row=1,column=1,rowspan=2,padx=(0,40),sticky="e")

    def show_login_voice_auth_screen(self):
        self.login_flow_state = 'voice_auth'
        username = simpledialog.askstring("Username", "Enter your username to verify:", parent=self.root)
        if not username:
            self.show_home_screen(); return
        self.login_attempt_user = username.lower()
        
        card = self._create_main_card(width=600, height=350); self._update_nav_selection("home")
        tk.Label(card,text=f'Please say "{self.enrollment_phrase}"',font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(expand=True)
        mic_label = tk.Label(card, image=self.mic_img, bg=CARD_BG_COLOR, cursor="hand2"); mic_label.pack(expand=True)
        mic_label.bind("<Button-1>", self.handle_login_voice_record)
        self.recording_status_label=tk.Label(card,text="Click the mic to authenticate",font=self.font_small,fg=TEXT_COLOR,bg=CARD_BG_COLOR);self.recording_status_label.pack(pady=(0, 20))

    def handle_login_voice_record(self, event=None):
        self.recording_status_label.config(text="Recording for verification (4s)..."); self.root.update_idletasks()
        filepath = os.path.join(AUDIO_DIR, f"verify_{self.login_attempt_user}.wav")
        self._record_audio_blocking(filepath, duration=4)
        
        self.recording_status_label.config(text="Verifying with server..."); self.root.update_idletasks()
        
        response = self.api.verify_voice(self.login_attempt_user, filepath)
        
        if response.get("verified"):
            messagebox.showinfo("Success", f"Voice Authenticated!\nSimilarity: {response.get('score', 0):.3f}")
            self.show_password_screen()
        else:
            messagebox.showerror("Failure", f"Voice authentication failed.\n{response.get('message', 'Please try again.')}")
            self.show_home_screen()

    def show_password_screen(self):
        self.login_flow_state = 'password_entry';card=self._create_main_card(width=500,height=350);self._update_nav_selection("home");content_wrapper=tk.Frame(card,bg=CARD_BG_COLOR);content_wrapper.pack(expand=True);tk.Label(content_wrapper,text="Enter Password",font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(pady=(20,10));self.error_label=tk.Label(content_wrapper,text="",font=self.font_small,fg=ERROR_COLOR,bg=CARD_BG_COLOR);self.error_label.pack(pady=(0,10));self.password_entry=tk.Entry(content_wrapper,font=self.font_large,fg=TEXT_COLOR,bg=GRADIENT_TOP_COLOR,show="*",width=25,relief="solid",borderwidth=1,justify="center");self.password_entry.pack(pady=10,ipady=5);self.password_entry.focus_set();tk.Button(content_wrapper,text="Confirm",font=self.font_normal,bg=BUTTON_COLOR,fg=TEXT_COLOR,relief="flat",borderwidth=0,padx=20,pady=5,command=self.check_password).pack(pady=(20,15));forgot_link=tk.Label(content_wrapper,text="Forgot Password?",font=self.font_small,fg=TEXT_COLOR,bg=CARD_BG_COLOR,cursor="hand2");forgot_link.pack();forgot_link.bind("<Button-1>",lambda e: messagebox.showinfo("Info", "Password reset is handled by the backend.\n(This feature is not yet implemented in the API.)"))

    def check_password(self):
        password = self.password_entry.get()
        if not self.login_attempt_user or not password:
            self.error_label.config(text="An error occurred."); return

        response = self.api.login(self.login_attempt_user, password)
        if response.get("login_success"):
            self.currently_logged_in_user = response.get("user_details")
            self.login_attempt_user = None
            self.show_home_screen()
        else:
            self.error_label.config(text=response.get("message", "Incorrect Password."))
            self.password_entry.delete(0, 'end')

    def show_applications_screen(self):
        self._update_nav_selection("applications")
        card = self._create_main_card(width=600, height=300)
        if self.currently_logged_in_user:
            tk.Label(card, text=f"Welcome, {self.currently_logged_in_user.get('full_name')}!", font=self.font_large_bold, fg=TEXT_COLOR, bg=CARD_BG_COLOR).pack(pady=20)
            tk.Label(card, text="Application and settings management\nvia a web portal is coming soon.", font=self.font_normal, fg=TEXT_COLOR, bg=CARD_BG_COLOR).pack(expand=True)
        else:
            tk.Label(card, text="Please log in to manage application settings.", font=self.font_large, fg=TEXT_COLOR, bg=CARD_BG_COLOR, wraplength=400).pack(expand=True)
    
    # --- Enrollment Flow  ---
    def navigate_to_enrollment(self, event=None):
        self.show_enrollment_step1()

    def show_enrollment_step1(self):
        self.enrollment_state='step1_account_setup';self.new_enrollment_data={};card=self._create_main_card(width=700,height=450);self._update_nav_selection("enrollment");tk.Label(card,text="STEP 1: Account Setup",font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=0,column=0,columnspan=2,sticky="w",pady=(20,5),padx=40);tk.Label(card,text="Enter your basic account information",font=self.font_normal,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=1,column=0,columnspan=2,sticky="w",pady=(0,25),padx=40);fields={"Full Name:":"full_name","Username:":"username","Password:":"password","Confirm Password:":"confirm_password", "Email:": "email"};self.entry_widgets={}
        for i,(label,key) in enumerate(fields.items()):
            tk.Label(card,text=label,font=self.font_large,fg=TEXT_COLOR,bg=CARD_BG_COLOR).grid(row=i+2,column=0,sticky="w",pady=8,padx=(40,20));entry=tk.Entry(card,font=self.font_large,width=25,bg=GRADIENT_TOP_COLOR,fg=TEXT_COLOR,relief="solid",bd=1);self.entry_widgets[key]=entry
            if"Password"in label:entry.config(show="*")
            entry.grid(row=i+2,column=1,pady=8,ipady=4,padx=(0,40))
        self.enroll_error_label=tk.Label(card,text="",font=self.font_small,fg=ERROR_COLOR,bg=CARD_BG_COLOR);self.enroll_error_label.grid(row=len(fields)+2,column=0,columnspan=2,pady=(10,0));bf=tk.Frame(self.content_frame,bg="#7c2e50");bf.pack(fill="x",padx=60,pady=(0,10));tk.Label(bf,text="● ○",font=self.font_large,fg=TEXT_COLOR,bg="#7c2e50").pack(side="left");tk.Button(bf,text="Next Step →",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",padx=15,pady=5,command=self._validate_step1).pack(side="right")
    
    def _validate_step1(self):
        data = {key: entry.get() for key, entry in self.entry_widgets.items()}
        if not all(v for k, v in data.items() if k != 'confirm_password'):
            self.enroll_error_label.config(text="All fields (except confirm) are required."); return
        if data["password"] != data["confirm_password"]:
            self.enroll_error_label.config(text="Passwords do not match."); return
        
        reg_data = {k: v for k, v in data.items() if k != 'confirm_password'}
        response = self.api.register_user(reg_data)

        if response.get("status") == "success":
            self.new_enrollment_data = reg_data
            self.enroll_error_label.config(text="")
            self.show_enrollment_step2()
        else:
            self.enroll_error_label.config(text=response.get("message", "Registration failed."))

    def show_enrollment_step2(self):
        card = self._create_main_card(width=700, height=350)
        self._update_nav_selection("enrollment")
        tk.Label(card,text="STEP 2: Voice Enrollment",font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR).pack(anchor="w",pady=(20,5), padx=40)
        tk.Label(card,text="Record a 5-second sample of your voice saying the phrase below.\nThis allows the system to create your unique voiceprint.",font=self.font_normal,fg=TEXT_COLOR,bg=CARD_BG_COLOR, justify="left").pack(anchor="w",pady=(0,25), padx=40)
        tk.Label(card,text=f'"{self.enrollment_phrase}"',font=self.font_large_bold,fg=TEXT_COLOR,bg=CARD_BG_COLOR,wraplength=500).pack(expand=True)
        mic_label = tk.Label(card,image=self.mic_img,bg=CARD_BG_COLOR,highlightthickness=0,cursor="hand2");mic_label.pack(pady=10)
        mic_label.bind("<Button-1>", self.handle_enrollment_recording)
        self.recording_status_label=tk.Label(card,text="Click the mic to record",font=self.font_small,fg=TEXT_COLOR,bg=CARD_BG_COLOR);self.recording_status_label.pack(pady=(0,20));
        bf=tk.Frame(self.content_frame,bg="#7c2e50");bf.pack(fill="x",padx=60,pady=(0,10));tk.Button(bf,text="< Back",font=self.font_normal,bg=BUTTON_LIGHT_COLOR,fg=BUTTON_LIGHT_TEXT_COLOR,relief="flat",padx=15,pady=5,command=self.show_enrollment_step1).pack(side="left");tk.Label(bf,text="○ ●",font=self.font_large,fg=TEXT_COLOR,bg="#7c2e50").pack(side="left",padx=20)
    
    def handle_enrollment_recording(self, event=None):
        username = self.new_enrollment_data.get("username")
        if not username: messagebox.showerror("Error", "Username is missing from enrollment data."); return
        
        self.recording_status_label.config(text="Recording for enrollment (5s)..."); self.root.update_idletasks()
        filepath = os.path.join(AUDIO_DIR, f"enroll_{username}.wav")
        self._record_audio_blocking(filepath, duration=5)

        self.recording_status_label.config(text="Sending to server..."); self.root.update_idletasks()
        response = self.api.enroll_voice(username, filepath)

        if response.get("status") == "success":
            messagebox.showinfo("Success", "Enrollment complete! You will now be taken to the login screen.")
            self.just_enrolled = True
            self.enrollment_state = 'not_started'
            self.login_attempt_user = username
            self.show_home_screen()
        else:
            messagebox.showerror("Enrollment Failed", response.get("message", "An error occurred during voice processing."))

    # --- AUDIO & UTILITIES (Refactored) ---
    def _record_audio_blocking(self, filepath, duration):
        stream = self.pyaudio_instance.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * duration))]
        stream.stop_stream(); stream.close()
        
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(CHANNELS); wf.setsampwidth(self.pyaudio_instance.get_sample_size(FORMAT)); wf.setframerate(RATE); wf.writeframes(b''.join(frames))
        print(f"Audio saved to {filepath}")

    def _on_closing(self):
        self.pyaudio_instance.terminate()
        self.root.destroy()
        
if __name__ == "__main__":
    # This block is the entry point when you run `python app.py`

    # First, create the main Tkinter window object.
    root = tk.Tk()
    
    # Then, create an instance of your application class, passing the window to it.
    app = KeyVoxApp(root)
    
    # Finally, and most importantly, start the Tkinter event loop.
    # This draws the window and keeps the application running.
    root.mainloop()