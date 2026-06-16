"""
email.py — Email Utility

Provides transactional email functions used as background tasks across the API.
All emails are sent via SMTP using credentials loaded from .env.
Designed to be called with FastAPI BackgroundTasks — execution happens after
the HTTP response is returned so the client is never blocked.

Configuration (required in .env):
    MAIL_HOST      — SMTP server hostname (e.g. sandbox.smtp.mailtrap.io)
    MAIL_PORT      — SMTP port (2525 recommended for dev)
    MAIL_USERNAME  — SMTP username
    MAIL_PASSWORD  — SMTP password
"""
from datetime import datetime
import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")

MAIL_HOST = os.getenv("MAIL_HOST", "")
MAIL_PORT = int(os.getenv("MAIL_PORT", "2525"))
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")

logger = logging.getLogger(__name__)


def send_welcome_email(to_email: str, member_name: str) -> None:
    """Send a welcome email to a newly registered gym member.

    Builds a plain-text MIME message and delivers it via SMTP using
    credentials from .env. Intended to run as a FastAPI background task —
    called after the member is saved so the HTTP response is not delayed.

    Args:
        to_email: The new member's email address.
        member_name: The new member's name — used to personalise the greeting.

    Returns:
        None

    Note:
        SMTP failures are logged and swallowed. Email is best-effort and never
        propagates out of this background task, so a dead mail server cannot fail
        the request that scheduled it.
    """

    message = MIMEMultipart()

    message["Subject"] = "Welcome to our community"
    message["From"] = "noreply@anytimefitness.com"
    message["To"] = to_email
    body = f"Hi {member_name}, Welcome to anytime fitness, we are excited to help you through your fitness journey. Enjoy!!"
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(MAIL_HOST, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(message["From"], to_email, message.as_string())
    except Exception:
        # Email is best-effort: log it so the failure is observable, but never crash
        # the background task (and therefore never affect the original request).
        logger.warning("email send failed for %s", to_email, exc_info=True)


def send_session_notification(to_email: str, trainer: str, member_name: str, gym_name: str, schedule_at: datetime) -> None:
    """Send a session notification email to a member when they are added to a workout session.

    Intended to run as a FastAPI background task — called after the attendance
    record is saved so the HTTP response is not delayed.

    Args:
        to_email: The member's email address.
        trainer: The trainer's name leading the session.
        member_name: The member's name — used to personalise the greeting.
        gym_name: The gym where the session takes place.
        schedule_at: The scheduled date and time of the session.

    Returns:
        None

    Note:
        SMTP failures are logged and swallowed. Email is best-effort and never
        propagates out of this background task, so a dead mail server cannot fail
        the request that scheduled it.
    """
    date_str = schedule_at.strftime("%B %d, %Y")
    time_str = schedule_at.strftime("%H:%M")

    message = MIMEMultipart()

    message["Subject"] = "session alert"
    message["From"] = "noreply@anytimefitness.com"
    message["To"] = to_email
    body = f"""Hi {member_name}, 
    your have a personal training session with coach {trainer}. 
    Date: {date_str}
    Time: {time_str}
    Location :{gym_name} """
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(MAIL_HOST, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(message["From"], to_email, message.as_string())
    except Exception:
        # Email is best-effort: log it so the failure is observable, but never crash
        # the background task (and therefore never affect the original request).
        logger.warning("email send failed for %s", to_email, exc_info=True)
