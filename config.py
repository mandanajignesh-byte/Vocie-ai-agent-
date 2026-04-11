"""Central configuration — loaded once, imported everywhere."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ── Models ────────────────────────────────────────────────────────────────────
STT_MODEL: str = os.getenv("STT_MODEL", "whisper-large-v3")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
KB_PATH = BASE_DIR / "knowledge_base" / "autostream.json"

OUTPUT_DIR.mkdir(exist_ok=True)
