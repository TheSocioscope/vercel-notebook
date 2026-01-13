"""
Configuration for Socioscope application.
"""
import os
from dotenv import load_dotenv

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

MODELS = [
    ("Qwen3-32B", "qwen/qwen3-32b"),
    ("Llama Guard 4-12B", "meta-llama/llama-guard-4-12b"),
    ("GPT-OSS 120B", "openai/gpt-oss-120b"),
    ("GPT-OSS 20B", "openai/gpt-oss-20b"),
    ("Llama 4 Maverick 17B-128E Instruct", "meta-llama/llama-4-maverick-17b-128e-instruct"),
    ("Llama 4 Scout 17B-16E Instruct", "meta-llama/llama-4-scout-17b-16e-instruct"),
    ("Kimi K2 Instruct 0905", "moonshotai/kimi-k2-instruct-0905"),
]
