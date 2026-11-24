import os
import smtplib
from email.message import EmailMessage


def send_welcome_email(receiver_email: str, username: str):
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    sender = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    if not all([host, port, sender, password]):
        return False, "SMTP not configured, welcome email skipped."

    try:
        msg = EmailMessage()
        msg["Subject"] = "Welcome to Math Solver Studio"
        msg["From"] = sender
        msg["To"] = receiver_email
        msg.set_content(f"""Hi {username},

Welcome to Math Solver Studio. Your account is ready.

You can ask questions by typing, using your voice, or uploading a question file. You can also practise topic-wise questions in easy, medium, and hard levels.

Best wishes,
Math Solver Studio""")
        with smtplib.SMTP(host, int(port)) as smtp:
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(msg)
        return True, "Welcome email sent."
    except Exception as exc:
        return False, f"Welcome email skipped: {exc}"
