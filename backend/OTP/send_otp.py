import smtplib
import ssl
import secrets
import os
import time
from OTP import otp_settings as settings

# --- Always use absolute paths relative to this script's location ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EMAIL_FILE = os.path.join(BASE_DIR, "OTP_Email.txt")
OTP_FILE = os.path.join(BASE_DIR, "OTP_CurrentOTP.txt")
OTP_TIME_FILE = os.path.join(BASE_DIR, "OTP_Timestamp.txt")  # to track when OTP was generated



# 🔹 Add this helper section here (before any OTP logic)

def ensure_file_exists(file_path, description):
    """Ensure the given file exists and notify the user if it was created."""
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("")  # create empty file
        print(f"{description} was missing, so I created it at:\n{os.path.abspath(file_path)}\nPlease update it if needed.")
        return False
    return True


def ensure_all_files():
    """Check all OTP-related files and show their locations if created."""
    ensure_file_exists(EMAIL_FILE, "OTP_Email.txt (for recipient email)")
    ensure_file_exists(OTP_FILE, "OTP_CurrentOTP.txt (for current OTP)")
    ensure_file_exists(OTP_TIME_FILE, "OTP_Timestamp.txt (for OTP timestamp)")


# 🔹 Keep your original ensure_email_file, but slightly update it:
def ensure_email_file():
    """Ensure that OTP_Email.txt exists and contains a recipient email."""
    ensure_file_exists(EMAIL_FILE, "OTP_Email.txt (for recipient email)")

    with open(EMAIL_FILE, "r") as f:
        recipient_email = f.read().strip()

    if not recipient_email:
        print(f"{os.path.abspath(EMAIL_FILE)} is empty. Please add an email address to send OTP.")
        return None

    return recipient_email


# --- The rest of your code stays the same ---
def generate_otp():
    """Generate a secure 6-digit OTP."""
    return str(secrets.randbelow(10**6)).zfill(6)


def save_otp(otp):
    """Save OTP and timestamp to file."""
    with open(OTP_FILE, "w") as f:
        f.write(otp)
    with open(OTP_TIME_FILE, "w") as f:
        f.write(str(int(time.time())))  # store current time in seconds
    return OTP_FILE


def load_otp():
    """Load OTP and timestamp from file safely."""
    if not os.path.exists(OTP_FILE) or not os.path.exists(OTP_TIME_FILE):
        return None, None

    # Load OTP
    with open(OTP_FILE, "r") as f:
        otp = f.read().strip()
        if not otp:
            otp = None

    # Load timestamp safely
    with open(OTP_TIME_FILE, "r") as f:
        ts_str = f.read().strip()
        try:
            timestamp = int(ts_str) if ts_str else None
        except ValueError:
            timestamp = None

    return otp, timestamp



def format_email(recipient_email, otp):
    """Format email content with subject and body."""
    subject = "Your One-Time Password (OTP)"
    body = f"""
    Dear User,

    Your One-Time Password (OTP) is: {otp}

    Please do not share this OTP with anyone.
    It is valid for {settings.OTP_VALIDITY_MINUTES} minutes.

    If you did not request this OTP, please ignore this email.

    Sincerely,
    Your Security Team
    """
    return f"Subject: {subject}\nTo: {recipient_email}\n\n{body}"


def send_email(recipient_email, message):
    """Send email via SMTP server."""
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, context=context) as server:
        server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)
        server.sendmail(settings.SENDER_EMAIL, recipient_email, message)
    print(f"OTP sent successfully to {recipient_email}.")


def send_otp(recipient_email):
    """
    Generate, save, and send OTP to the given recipient_email.
    Handles cooldown and email comparison automatically.
    Returns (success: bool, message: str)
    """
    try:
        ensure_all_files()

        # --- Load previous email (if any) ---
        old_email = None
        if os.path.exists(EMAIL_FILE):
            with open(EMAIL_FILE, "r") as f:
                old_email = f.read().strip()

        otp, timestamp = load_otp()
        current_time = time.time()

        # --- Cooldown logic (only if same email and OTP still valid) ---
        if otp and timestamp and old_email == recipient_email:
            elapsed_minutes = (current_time - timestamp) / 60
            if elapsed_minutes < settings.OTP_VALIDITY_MINUTES:
                remaining = int(settings.OTP_VALIDITY_MINUTES - elapsed_minutes)
                message = f"⏳ OTP already sent to {recipient_email}. Please wait {remaining} minute(s)."
                print(message)
                return True, message  # OTP still valid, no resend

        # --- Generate new OTP ---
        otp = generate_otp()
        message = format_email(recipient_email, otp)

        try:
            # Try sending email first
            send_email(recipient_email, message)
        except Exception as e:
            error_msg = f"❌ Failed to send OTP to {recipient_email}: {e}"
            print(error_msg)
            return False, error_msg

        # ✅ Only if email was sent successfully, then save OTP and email
        save_otp(otp)
        with open(EMAIL_FILE, "w") as f:
            f.write(recipient_email)

        success_msg = f"✅ OTP sent successfully to {recipient_email}."
        print(success_msg)
        return True, success_msg

    except Exception as e:
        error_msg = f"❌ Unexpected error sending OTP to {recipient_email}: {e}"
        print(error_msg)
        return False, error_msg



def verify_otp(user_input):
    """Verify if user input matches the stored OTP and is still valid."""
    otp, timestamp = load_otp()
    if not otp or not timestamp:
        print("No OTP found. Please request a new one.")
        return False

    # Check expiration
    elapsed_minutes = (time.time() - timestamp) / 60
    if elapsed_minutes > settings.OTP_VALIDITY_MINUTES:
        print("OTP has expired. Please request a new one.")
        return False

    if user_input == otp:
        print("OTP verification successful!")
        
        # ✅ Delete OTP after successful verification
        if os.path.exists(OTP_FILE):
            os.remove(OTP_FILE)
        if os.path.exists(OTP_TIME_FILE):
            os.remove(OTP_TIME_FILE)
        
        return True
    else:
        print("Invalid OTP. Please try again.")
        return False



if __name__ == "__main__":
    send_otp()
    