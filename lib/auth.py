import os
import json
import time
from cryptography.fernet import Fernet, InvalidToken
from dataclasses import dataclass

# Token validity in seconds (5 minutes)
TOKEN_VALIDITY = 5 * 60

# Allowed email domains
ALLOWED_DOMAINS = ["@paris-iea.fr", "@csh.ac.at"]


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


def generate_magic_link(email: str, base_url: str = "http://localhost:5001") -> str:
    """Generate a magic link token containing email + timestamp."""
    payload = json.dumps({"email": email, "ts": time.time()})
    token = get_fernet().encrypt(payload.encode()).decode()
    link = f"{base_url}/auth?token={token}"

    # Print the link (later: send via email)
    print(f"\n{'='*50}")
    print(f"MAGIC LINK for {email}:")
    print(link)
    print(f"{'='*50}\n")

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

        # Check if token is expired (5 min)
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
