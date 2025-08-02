import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def test_smtp_email_connection():
    """
    Test SMTP connection and optionally send a test email.

    Skips if SMTP_SERVER or EMAIL_PASSWORD are not set in .env
    """
    if not (SMTP_SERVER and EMAIL_FROM and EMAIL_TO and EMAIL_PASSWORD):
        print("⚠️ Skipping email test because SMTP credentials are missing.")
        return

    try:
        # Connect and authenticate
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)

            # Compose and send a test message
            msg = MIMEText("✅ Test email from ResearchAssistant test suite.")
            msg["Subject"] = "ResearchAssistant Email Test"
            msg["From"] = EMAIL_FROM
            msg["To"] = EMAIL_TO

            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())

        print("✅ Email test passed and test message sent successfully!")

    except Exception as e:
        raise AssertionError(f"Email test failed: {e}")
