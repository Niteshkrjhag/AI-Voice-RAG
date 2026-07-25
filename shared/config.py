"""
shared/config.py — Centralized configuration loader

Loads all environment variables from .env file and exposes them
as typed attributes on a single Config object. Every module in the
project imports from here instead of reading os.environ directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# ── Locate and load .env from project root ──────────────────────
# Path.resolve() converts relative to absolute, parents[1] goes
# from shared/ -> project root
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ENV_PATH = _PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


class Config:
    """
    Immutable configuration singleton.
    All values sourced from environment variables with sensible defaults.
    """

    # ── Google Gemini (Primary LLM) ─────────────────────────────
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # ── Vapi (Voice Platform) ──────────────────────────────────
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")
    VAPI_PHONE_NUMBER_ID: str = os.getenv("VAPI_PHONE_NUMBER_ID", "")

    # ── Qdrant (Vector Database) ────────────────────────────────
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION_NAME: str = os.getenv(
        "QDRANT_COLLECTION_NAME", "health_insurance_kb"
    )

    # ── AssemblyAI (Streaming ASR) ──────────────────────────────
    ASSEMBLYAI_API_KEY: str = os.getenv("ASSEMBLYAI_API_KEY", "")

    # ── Embedding Configuration ─────────────────────────────────
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))

    # ── Application Settings ────────────────────────────────────
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    RETRIEVAL_API_HOST: str = os.getenv("RETRIEVAL_API_HOST", "0.0.0.0")
    RETRIEVAL_API_PORT: int = int(os.getenv("RETRIEVAL_API_PORT", "8000"))
    WEBSOCKET_HOST: str = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
    WEBSOCKET_PORT: int = int(os.getenv("WEBSOCKET_PORT", "8765"))

    # ── Derived Paths ───────────────────────────────────────────
    PROJECT_ROOT: Path = _PROJECT_ROOT
    DATA_RAW_DIR: Path = _PROJECT_ROOT / "q2_knowledge_base" / "data" / "raw"
    DATA_CLEANED_DIR: Path = _PROJECT_ROOT / "q2_knowledge_base" / "data" / "cleaned"
    DATA_INDEXED_DIR: Path = _PROJECT_ROOT / "q2_knowledge_base" / "data" / "indexed"
    
    def validate(self):
        """SDE-3: Fast-fail validation to prevent silent crashes later."""
        required_keys = ["GOOGLE_API_KEY", "VAPI_API_KEY", "ASSEMBLYAI_API_KEY", "QDRANT_API_KEY"]
        missing = [key for key in required_keys if not getattr(self, key)]
        if missing:
            raise ValueError(f"CRITICAL: Missing required environment variables in .env: {', '.join(missing)}")


# ── Module-level singleton ──────────────────────────────────────
# Import as: from shared.config import config
config = Config()

# SDE-3: Validate configuration immediately on boot
config.validate()
