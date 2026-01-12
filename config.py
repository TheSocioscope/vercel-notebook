"""
Configuration and database setup for Socioscope application.
"""
import os
from dotenv import load_dotenv
from fastlite import database
from lib.sources import Source
from lib.discussion import Message

load_dotenv()

# Session security configuration
SESSION_SECRET = os.getenv("SESSION_SECRET")
if not SESSION_SECRET:
    raise ValueError("SESSION_SECRET env var not set - generate with: python -c \"import secrets; print(secrets.token_hex(32))\"")
IS_PRODUCTION = os.getenv("VERCEL_ENV") == "production"

# Database configuration
DB_NAME = "socioscope_db"
COLLECTION_NAME = "socioscope_documents"
MAX_SESSION_AGE = 7 * 24 * 3600  # days x hours x minutes

# Initialize in-memory database
db = database(":memory:")
sources = db.create(Source, pk="filename")
discussion = db.create(Message, pk="order")
