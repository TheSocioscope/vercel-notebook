import os
import json
import time
import boto3
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet, InvalidToken
from dataclasses import dataclass

# Token validity in seconds (shorter = more secure)
TOKEN_VALIDITY = 2 * 60  # 2 minutes

# Allowed email domains
ALLOWED_DOMAINS = ["@paris-iea.fr", "@csh.ac.at"]

# SES configuration
SES_REGION = os.getenv("AWS_SES_REGION", "")
SES_SENDER = os.getenv("SES_SENDER_EMAIL", "vercel@thesocioscope.org")


def is_email_allowed(email: str) -> bool:
    """Check if email is from an allowed domain."""
    email = email.strip().lower()
    return any(email.endswith(domain) for domain in ALLOWED_DOMAINS)


# Lazy-loaded Fernet instance
_fernet = None


def get_fernet() -> Fernet:
    """Get Fernet cipher (lazy-loaded from env)."""
    global _fernet
    if _fernet is None:
        secret = os.getenv("MAGIC_SECRET")
        if not secret:
            raise ValueError("MAGIC_SECRET env var not set")
        _fernet = Fernet(secret.encode())
    return _fernet


def send_magic_link_email(email: str, magic_link: str) -> bool:
    """Send magic link via Amazon SES. Returns True on success."""
    ses = boto3.client("ses", region_name=SES_REGION)

    subject = "Your Socioscope Login Link"
    body_text = f"""Hi,

Click the link below to log in to Socioscope:

{magic_link}

This link expires in 2 minutes.

If you didn't request this, you can safely ignore this email.
"""
    body_html = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px;">
        <h2 style="color: #333;">Socioscope Login</h2>
        <p>Click the button below to log in:</p>
        <a href="{magic_link}" 
           style="display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; 
                  text-decoration: none; border-radius: 6px; margin: 16px 0;">
            Log In to Socioscope
        </a>
        <p style="color: #666; font-size: 14px;">This link expires in 2 minutes.</p>
        <p style="color: #999; font-size: 12px;">If you didn't request this, you can safely ignore this email.</p>
    </body>
    </html>
    """

    try:
        ses.send_email(
            Source=SES_SENDER,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": body_text, "Charset": "UTF-8"},
                    "Html": {"Data": body_html, "Charset": "UTF-8"},
                },
            },
        )
        print(f"Magic link email sent to {email}")
        return True
    except ClientError as e:
        print(f"Failed to send email to {email}: {e.response['Error']['Message']}")
        return False


def generate_magic_link(email: str, base_url: str = "http://localhost:5001") -> str:
    """Generate a magic link token and send it via email."""
    payload = json.dumps({"email": email, "ts": time.time()})
    token = get_fernet().encrypt(payload.encode()).decode()
    link = f"{base_url}/auth?token={token}"

    # Send via SES
    send_magic_link_email(email, link)

    return link


def verify_token(token: str) -> tuple[bool, str]:
    """
    Verify a magic link token.
    Returns (success, message_or_email).
    """
    try:
        payload = get_fernet().decrypt(token.encode()).decode()
        data = json.loads(payload)

        email = data.get("email")
        ts = data.get("ts")

        if not email or not ts:
            return False, "Invalid token format"

        # Check if token is expired
        age = time.time() - ts
        if age > TOKEN_VALIDITY:
            return False, f"Token expired ({int(age)}s old, max {TOKEN_VALIDITY}s)"

        return True, email

    except InvalidToken:
        return False, "Invalid or corrupted token"
    except Exception as e:
        return False, f"Token verification failed: {e}"


@dataclass
class MagicLinkRequest:
    email: str
