"""Settings, read once from backend/.env. Nothing here ever returns a secret's value to a caller
that could show it: the health check only learns whether a key is present."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")

# APP_DB_PATH lets checks run against a throwaway database. Normally unset.
DB_PATH = Path(os.environ.get("APP_DB_PATH") or PROJECT_DIR / "data" / "app.sqlite3")
PROMPT_FILE = PROJECT_DIR / "prompts" / "breathing-guide.md"

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
MODEL_MODES = ("live", "mock", "fail")


def gemini_api_key() -> str | None:
    value = os.getenv("GEMINI_API_KEY", "").strip()
    return value or None


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_GEMINI_MODEL


def demo_modes_allowed() -> bool:
    """Whether a request may ask for the mocked or failing model (for demos and checks)."""
    return os.getenv("ALLOW_DEMO_MODES", "").strip() == "1"


def key_status() -> str:
    return "key is configured" if gemini_api_key() else "key is not configured"
