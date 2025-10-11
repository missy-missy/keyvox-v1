    # # =========================================================
    # # USER PROFILE PAGE
    # # =========================================================
    # def show_user_profile(self):
    #     self.clear_content()
    #     ctk.CTkLabel(self.content_frame, text="User Profile",
    #                  text_color=PINK, font=ctk.CTkFont(size=26, weight="bold")).pack(pady=30)

    #     fields = {
    #         "Name": "Ashley Jewel Heart Malasa",
    #         "Username": "ashley_m",
    #         "Email Address": "ashley.m@example.com",
    #         "Date of Enrollment": "October 5, 2025"
    #     }

    #     for key, value in fields.items():
    #         row = ctk.CTkFrame(self.content_frame, fg_color=CARD_COLOR, corner_radius=10)
    #         row.pack(pady=8, padx=250, fill="x")
    #         ctk.CTkLabel(row, text=f"{key}:", text_color="white",
    #                      font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10, pady=10)
    #         ctk.CTkLabel(row, text=value, text_color="gray80",
    #                      font=ctk.CTkFont(size=14)).pack(side="right", padx=10, pady=10)

    #     ctk.CTkButton(self.content_frame, text="Deactivate Account",
    #                   fg_color=PINK, hover_color=LIGHT_PINK,
    #                   width=220, height=40, corner_radius=25,
    #                   command=self.show_welcome_page).pack(pady=40)