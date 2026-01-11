import os
from dataclasses import dataclass


@dataclass
class LoginRequest:
    username: str
    password: str


def verify_credentials(username: str, password: str) -> bool:
    """Check username and password against environment variables."""
    expected_user = os.getenv("APP_USERNAME")
    expected_pass = os.getenv("APP_PASSWORD")
    
    if not expected_user or not expected_pass:
        raise ValueError("APP_USERNAME and APP_PASSWORD env vars must be set")
    
    return username == expected_user and password == expected_pass
