"""
Configuration for AI Layer.

Handles API keys, LLM provider settings, and system defaults.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """AI Layer configuration settings."""
    
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic")
    
    DEFAULT_TIME_HORIZON_MONTHS: int = 60
    MAX_TIME_HORIZON_MONTHS: int = 120
    MIN_TIME_HORIZON_MONTHS: int = 12
    
    DEFAULT_N_PATHS: int = 5000
    MIN_N_PATHS: int = 1000
    MAX_N_PATHS: int = 10000
    
    OUTPUT_DIR: Path = Path(__file__).parent / "outputs"
    CHART_DIR: Path = OUTPUT_DIR / "charts"
    
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    MAX_QUERY_LENGTH: int = 2000
    MAX_USER_DATA_SIZE: int = 10000
    
    ENABLE_CACHING: bool = os.getenv("ENABLE_CACHING", "false").lower() == "true"
    
    @classmethod
    def ensure_output_dirs(cls):
        """Create output directories if they don't exist."""
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.CHART_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def has_llm_provider(cls) -> bool:
        """Check if any LLM provider is configured."""
        return bool(cls.ANTHROPIC_API_KEY or cls.OPENAI_API_KEY)
    
    @classmethod
    def get_available_provider(cls) -> Optional[str]:
        """Get first available LLM provider."""
        if cls.ANTHROPIC_API_KEY:
            return "anthropic"
        elif cls.OPENAI_API_KEY:
            return "openai"
        return None


Config.ensure_output_dirs()
