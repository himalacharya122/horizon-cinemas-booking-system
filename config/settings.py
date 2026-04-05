"""
config/settings.py
Centralised application settings loaded from .env file.
All other modules import from here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load .env
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


# Database
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
DB_NAME: str = os.getenv("DB_NAME", "hcbs")
DB_USER: str = os.getenv("DB_USER", "root")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
ENCODED_PASSWORD = quote_plus(DB_PASSWORD)

DATABASE_URL: str = (
    f"mysql+pymysql://{DB_USER}:{ENCODED_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

# JWT
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE-ME")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480")
)

# App
API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")