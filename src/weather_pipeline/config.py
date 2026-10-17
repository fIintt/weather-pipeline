import os

from dotenv import load_dotenv

load_dotenv()


def require_env(name: str) -> str:
    # If the 'name' doesnt exist, it returns None instead of crashing the program, unlike os.environ[name]
    value = os.environ.get(name)

    if not value or not value.strip():
        raise ValueError(f"Required environment variable {name!r} is missing or empty")

    return value


# API
API_URL = "https://api.open-meteo.com/v1/forecast"
API_TIMEOUT = 10
API_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
API_ARCHIVE_TIMEOUT = 30

# Database
DB_USER = require_env("DB_USER")
DB_PASSWORD = require_env("DB_PASSWORD")
DB_HOST = require_env("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = require_env("DB_NAME")