"""
Runtime configuration, read from environment variables (optionally a backend/.env file).

Everything has a safe default so a fresh clone runs with no .env at all. The
local-LLM categorization stage is off by default and no model name is baked in:
whoever runs the app names a model their own Ollama install actually has.
See backend/.env.example.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# This file is backend/app/config.py, so the .env we want is backend/.env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Off by default: a fresh clone must not depend on an LLM being installed.
LLM_ENABLED = os.getenv("LLM_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}

# Local by design - transaction descriptions never leave the machine.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434").rstrip("/")

# Deliberately empty. Hardcoding one author's model would break everyone else.
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()

# Generous because the first call after a cold start pays the model load from
# disk into VRAM - that alone can exceed 30s for a ~9GB model. Warm calls that
# follow are a couple of seconds.
try:
    LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", 60))
except ValueError:
    LLM_TIMEOUT_SECONDS = 60.0


def llm_is_configured() -> bool:
    """
    True only when the LLM stage is both switched on and usable.

    Enabling the flag without naming a model is a no-op rather than an error, so
    a half-filled .env quietly degrades to plain keyword categorization.
    """
    return LLM_ENABLED and bool(LLM_MODEL)
