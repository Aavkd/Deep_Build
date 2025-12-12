"""
DeepBuild Configuration Module

Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class ExecutionMode(str, Enum):
    """Execution mode for command sandbox."""
    STRICT = "strict"      # Only workspace directory
    RELAXED = "relaxed"    # Allow parent directories (not recommended)


# =============================================================================
# Ollama Configuration
# =============================================================================

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "granite4:3b")
OLLAMA_MAX_CONTEXT_CHARS = int(os.getenv("OLLAMA_MAX_CONTEXT_CHARS", "100000"))


# =============================================================================
# Execution Configuration
# =============================================================================

EXECUTION_MODE = ExecutionMode(os.getenv("EXECUTION_MODE", "strict"))
EXECUTION_TIMEOUT = int(os.getenv("EXECUTION_TIMEOUT", "60"))  # seconds
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))


# =============================================================================
# Search Configuration (Support Tool)
# =============================================================================

SEARCH_TIMEOUT = int(os.getenv("SEARCH_TIMEOUT", "30"))
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "5"))


# =============================================================================
# Path Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent
WORKSPACE_ROOT = PROJECT_ROOT / "DeepBuild_Workspace"
PROMPTS_DIR = PROJECT_ROOT / "PROMPTS"


def get_config_summary() -> dict:
    """Get a summary of current configuration."""
    return {
        "ollama_host": OLLAMA_HOST,
        "ollama_model": OLLAMA_MODEL,
        "execution_mode": EXECUTION_MODE.value,
        "execution_timeout": EXECUTION_TIMEOUT,
        "workspace_root": str(WORKSPACE_ROOT),
    }
